"""Build and validate an archive-only Photo Mode patch; never writes game files."""
from pathlib import Path
import runpy, struct, json, hashlib, copy

base = Path(__file__).resolve().parent.parent
r = runpy.run_path(str(base/'work'/'inspect_photo_config.py'))
game = r['GAME']
original = (game/'d'/'config').read_bytes()
decoded = r['archive']
records = [m for m in r['matches'] if m['type']['Type'] == 'PhotomodeSystemConfig']
assert len(records) == 1
rec = records[0]
assert rec['toc']['asset_id'] == 'AED6101948AAFA54'
start = rec['archive_offset']
asset = decoded[start:start+rec['size']]
p, n = r['sections'](asset)[0xE501186F]
locations = {}
before = r['decode'](asset, asset[p:p+n], locations)
path = '.Cameras.Cameras[1].CameraType.Obj.CamData.TetherDistance'
loc = locations[path]
assert before['Cameras']['Cameras'][1]['Name'] == 'Free'
assert before['Cameras']['Cameras'][1]['CameraType']['Type'] == 'PhotomodeCameraFreeMovePrius'
assert before['Cameras']['Cameras'][1]['CameraType']['Obj']['CamData']['TetherDistance'] == 10
assert loc['type'] == 0 and loc['count'] == 1 and loc['last_field']
# The final uint8 occupies a four-byte padded tail. A uint16 fits without
# shifting any fields, section offsets, archive offsets or TOC metadata.
assert loc['object_end'] == loc['offset']+4
value_at = start+p+loc['offset']
type_at = start+p+loc['type_offset']
assert decoded[value_at:value_at+4] == b'\x0a\0\0\0'
patched = bytearray(decoded)
patched[type_at] = 1  # DAT1 serialized uint16
struct.pack_into('<H', patched, value_at, 1000)
newasset = patched[start:start+rec['size']]
after = r['decode'](newasset, newasset[p:p+n])
expected = copy.deepcopy(before)
expected['Cameras']['Cameras'][1]['CameraType']['Obj']['CamData']['TetherDistance'] = 1000
assert after == expected
changed_bytes = [i for i,(a,b) in enumerate(zip(decoded,patched)) if a != b]
assert changed_bytes == sorted([type_at,value_at,value_at+1])

magic, version, count, header_end, total = struct.unpack_from('<4IQ', original)
output = bytearray(original[:header_end])
changed_blocks = []
for i in range(count):
    offset, oldpos, size, compressed, kind = struct.unpack_from('<2Q2IB', original,32+32*i)
    assert kind == 3
    block = patched[offset:offset+size]
    if block == decoded[offset:offset+size]:
        comp = original[oldpos:oldpos+compressed]
    else:
        # Valid LZ4 block consisting of one final literal sequence.
        comp = bytearray([0xf0])
        length = len(block)-15
        while length >= 255:
            comp.append(255); length -= 255
        comp.append(length); comp.extend(block)
        changed_blocks.append(i)
    struct.pack_into('<2Q2I', output, 32+32*i,offset,len(output),size,len(comp))
    output.extend(comp)
assert len(changed_blocks) == 1
prepared = base/'work'/'config.tether1000.prepared'
prepared.write_bytes(output)
assert r['dsar'](prepared) == patched
outdir = base/'outputs'/'photo-mode-tether-1000'
backup = outdir/'backup'/'config'
backup.parent.mkdir(parents=True,exist_ok=True)
if backup.exists():
    assert backup.read_bytes() == original, 'Existing backup differs; refusing to replace it.'
else:
    backup.write_bytes(original)
manifest = {
    'game_config':str(game/'d'/'config'),
    'prepared_config':str(prepared),
    'backup':str(backup),
    'original_sha256':hashlib.sha256(original).hexdigest(),
    'patched_sha256':hashlib.sha256(output).hexdigest(),
    'toc_sha256':hashlib.sha256((game/'toc').read_bytes()).hexdigest(),
    'field':path,'before':10,'after':1000,
    'unchanged_light_camera_tether':15,
    'unchanged_root_free_move_tether':10,
    'changed_decompressed_bytes':changed_bytes,
    'changed_dsar_block':changed_blocks[0],
    'installed':False
}
(outdir/'change.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(manifest,indent=2))
