"""Package the verified camera asset; do not change the installed game or profile."""
import ast, copy, hashlib, json, struct, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart')
namespace = {}
tree = ast.parse((ROOT/'work'/'inspect_photo_config.py').read_text())
helpers = ast.Module(body=[node for node in tree.body if isinstance(node,(ast.Import,ast.ImportFrom,ast.FunctionDef))],type_ignores=[])
exec(compile(helpers,'inspect_photo_config.py','exec'),namespace)
dsar,sections,decode = [namespace[name] for name in ('dsar','sections','decode')]
manifest = json.loads((ROOT/'outputs'/'camera-controls'/'change.json').read_text(encoding='utf-8-sig'))
preset = Path(manifest['presets']['10']['file'])
assert hashlib.sha256(preset.read_bytes()).hexdigest() == manifest['presets']['10']['sha256']
original = Path(manifest['vanilla_backup'])
assert hashlib.sha256(original.read_bytes()).hexdigest() == manifest['vanilla_sha256']
asset_id = 0xAED6101948AAFA54
toc = (GAME/'toc').read_bytes()
tags = sections(toc[8:])
id_pos,id_size = tags[0x506D7B8A]
ids = [x[0] for x in struct.iter_unpack('<Q',toc[8+id_pos:8+id_pos+id_size])]
indexes = [i for i,value in enumerate(ids) if value == asset_id]
assert len(indexes) == 1
index = indexes[0]
span_pos,span_size = tags[0xEDE8ADA9]
spans = list(struct.iter_unpack('<II',toc[8+span_pos:8+span_pos+span_size]))
matches = [i for i,(start,count) in enumerate(spans) if start <= index < start+count]
assert len(matches) == 1
span = matches[0]
metadata_pos,_ = tags[0x65BCF461]
size,archive_index,offset,header = struct.unpack_from('<IIIi',toc,8+metadata_pos+16*index)
archive_pos,archive_size = tags[0x398ABFF0]
archive_records = toc[8+archive_pos:8+archive_pos+archive_size]
archive_name = archive_records[66*archive_index:66*archive_index+40].split(b'\0')[0].decode()
assert archive_name == 'd\\config', 'The camera already has an asset override; inspect it before packaging.'
assert offset == 10830144 and size == 263280
patched_archive,vanilla_archive = dsar(preset),dsar(original)
asset = bytes(patched_archive[offset:offset+size])
vanilla_asset = bytes(vanilla_archive[offset:offset+size])
assert sections(asset) == sections(vanilla_asset)
data_pos,data_size = sections(asset)[0xE501186F]
baseline = decode(vanilla_asset,vanilla_asset[data_pos:data_pos+data_size])
result = decode(asset,asset[data_pos:data_pos+data_size])
expected = copy.deepcopy(baseline)
expected['Cameras']['Cameras'][1]['CameraType']['Obj']['CamData'].update(
    TetherDistance=1000,MoveSpeed=20,RiseSpeed=10,Acceleration=10000)
assert result == expected, 'The package must change only the intended Free camera values.'
entry = f'{span}/{asset_id:016X}'
info = {'game':'RCRA','format_version':2,'name':'Photo Mode — 10x Speed and 1000 Tether',
        'author':'Tim / Codex','version':'1.0',
        'description':'Native Free camera: movement 10x, tether 1000. Shift boost requires the separate runtime helper.'}
destination = ROOT/'outputs'/'camera-controls'/'PhotoMode-10x-Tether1000.stage'
with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as package:
    package.writestr('info.json',json.dumps(info,indent=2)+'\n')
    # Stage V2 accepts raw asset data with no STG wrapper. Passing null header
    # preserves the original TOC header, which this same-size edit does not change.
    package.writestr(entry,asset)
with zipfile.ZipFile(destination) as package:
    assert package.testzip() is None
    assert package.namelist() == ['info.json',entry]
    assert package.read(entry) == asset
verification = {'package':destination.name,'package_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
                'asset_entry':entry,'asset_size':size,'asset_sha256':hashlib.sha256(asset).hexdigest(),
                'verified_changes':{'TetherDistance':1000,'MoveSpeed':20,'RiseSpeed':10,'Acceleration':10000},
                'installed_via_overstrike':False,'preserves_original_toc_header':True}
(destination.parent/'stage-verification.json').write_text(json.dumps(verification,indent=2)+'\n')
print(json.dumps(verification,indent=2))
