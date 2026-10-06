import ast,struct
from pathlib import Path
ns={};tree=ast.parse(Path('work/inspect_photo_config.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef))],type_ignores=[]),'helpers','exec'),ns)
for p in [Path('outputs/startup-repair/toc.steam-original'),Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\toc')]:
 d=p.read_bytes();off,n=ns['sections'](d[8:])[0x398ABFF0]
 print(p.name)
 for i in range(0,n,66):
  b=d[8+off+i:8+off+i+66];name=b[:40].split(b'\0')[0].decode()
  if name in ['d\\movie','d\\config'] or 'mods' in name:print(i//66,name,b.hex())
