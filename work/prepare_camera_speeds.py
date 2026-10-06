"""Prepare same-size, validated Photo Mode speed variants; never writes the game."""
from pathlib import Path
import runpy, struct, json, hashlib, copy

base = Path(__file__).resolve().parent.parent
r = runpy.run_path(str(base/'work'/'inspect_photo_config.py'))
game = r['GAME']
source = (game/'d'/'config').read_bytes()
assert hashlib.sha256(source).hexdigest() == '06ea0a8d8b53052bb46451c9cbc75e59c9078d0ed1b970b51161d857aa4dd23a'
decoded = r['archive']
rec, = [m for m in r['matches'] if m['type']['Type'] == 'PhotomodeSystemConfig']
assert rec['toc']['asset_id'] == 'AED6101948AAFA54'
start = rec['archive_offset']
asset = decoded[start:start+rec['size']]
p,n = r['sections'](asset)[0xE501186F]
locations = {}
before = r['decode'](asset,asset[p:p+n],locations)
prefix = '.Cameras.Cameras[1].CameraType.Obj.CamData.'
accel,rise,move,tether = [locations[prefix+k] for k in ['Acceleration','RiseSpeed','MoveSpeed','TetherDistance']]
assert [v['type'] for v in [accel,rise,move,tether]] == [1,0,0,1]
assert [v['offset'] for v in [rise,move,tether]] == [accel['offset']+2,accel['offset']+3,accel['offset']+4]
assert tether['object_end'] == accel['offset']+8
assert tether['last_field'] and all(v['count']==1 for v in [accel,rise,move,tether])
out = base/'outputs'/'camera-controls'
(out/'presets').mkdir(parents=True,exist_ok=True)
(out/'backup').mkdir(exist_ok=True)
(out/'backup'/'config.tether1000').write_bytes(source)
manifest = {'target':str(game/'d'/'config'),'source_sha256':hashlib.sha256(source).hexdigest(),
            'vanilla_backup':str(base/'outputs'/'photo-mode-tether-1000'/'backup'/'config'),
            'vanilla_sha256':'f659e13afe36c335d3ab54441898378164a51c2c469a1a368a51c8a005310bb3',
            'presets':{},'installed_multiplier':None}
for multiplier in [1,10,100,1000]:
    acceleration = min(65535,1000*multiplier)
    patched = bytearray(decoded)
    # Widen RiseSpeed and MoveSpeed from uint8 to uint16. Their two extra
    # bytes consume the existing padded tail, so all object lengths stay fixed.
    for v in [rise,move]: patched[start+p+v['type_offset']] = 1
    struct.pack_into('<4H',patched,start+p+accel['offset'],acceleration,multiplier,2*multiplier,1000)
    newasset = patched[start:start+rec['size']]
    expected = copy.deepcopy(before)
    cam = expected['Cameras']['Cameras'][1]['CameraType']['Obj']['CamData']
    cam.update(Acceleration=acceleration,RiseSpeed=multiplier,MoveSpeed=2*multiplier)
    assert r['decode'](newasset,newasset[p:p+n]) == expected
    assert patched[:start+p+accel['type_offset']] == decoded[:start+p+accel['type_offset']]
    assert patched[start+p+tether['object_end']:] == decoded[start+p+tether['object_end']:]
    magic,version,count,header_end,total = struct.unpack_from('<4IQ',source)
    result = bytearray(source[:header_end])
    changed = []
    for i in range(count):
        offset,oldpos,size,compressed,kind = struct.unpack_from('<2Q2IB',source,32+32*i)
        assert kind == 3
        block = patched[offset:offset+size]
        if block == decoded[offset:offset+size]: comp = source[oldpos:oldpos+compressed]
        else:
            comp=bytearray([0xf0]);length=len(block)-15
            while length>=255:comp.append(255);length-=255
            comp.append(length);comp.extend(block);changed.append(i)
        struct.pack_into('<2Q2I',result,32+32*i,offset,len(result),size,len(comp))
        result.extend(comp)
    assert changed == [44]
    path = out/'presets'/f'config.{multiplier}x'
    path.write_bytes(result)
    assert r['dsar'](path) == patched
    manifest['presets'][str(multiplier)] = {'file':str(path),'sha256':hashlib.sha256(result).hexdigest(),
                                           'MoveSpeed':2*multiplier,'RiseSpeed':multiplier,'Acceleration':acceleration,'TetherDistance':1000}
(out/'change.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(manifest,indent=2))
