import ast,struct,hashlib,json
from pathlib import Path
root=Path.cwd();game=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart')
ns={};tree=ast.parse((root/'work/inspect_photo_config.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef))],type_ignores=[]),'helpers','exec'),ns)
def read(path):
 d=path.read_bytes();s=ns['sections'](d[8:]);ip,n=s[0x506D7B8A];mp,m=s[0x65BCF461];return [x[0] for x in struct.iter_unpack('<Q',d[8+ip:8+ip+n])],list(struct.iter_unpack('<IIIi',d[8+mp:8+mp+m]))
a,ar=read(root/'outputs/startup-repair/toc.steam-original');b,br=read(game/'toc');assert a==b
changed=[f'{aid:016X}' for aid,x,y in zip(a,ar,br) if x!=y];assert changed==['AED6101948AAFA54'],changed
row={'phase':'NoIntro disabled','changed_assets':changed,'all_boot_movies_original':True,'camera_config_still_modded':True,'native_dll_unchanged':hashlib.sha256((game/'hid.dll').read_bytes()).hexdigest()=='97b9a29eed154973fb587e0fae965c441b9956096211523aa1f99ef1d6d03e81','startup_test':'pending'}
(root/'outputs/startup-repair/isolation-verification.json').write_text(json.dumps(row,indent=2));print(json.dumps(row,indent=2))
