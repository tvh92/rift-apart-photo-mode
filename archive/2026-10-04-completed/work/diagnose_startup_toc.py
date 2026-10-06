import ast,struct,hashlib,json
from pathlib import Path
root=Path.cwd();game=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart')
ns={};tree=ast.parse((root/'work/inspect_photo_config.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef))],type_ignores=[]),'helpers','exec'),ns)
paths=[game/'toc',game/'toc.BAK',root/'outputs/camera-controls/migration-backup/toc',root/'outputs/camera-controls/migration-backup/toc.BAK']
for path in paths:
 data=path.read_bytes();s=ns['sections'](data[8:]);ap,asz=s[0x398ABFF0];ip,isz=s[0x506D7B8A];mp,_=s[0x65BCF461]
 archives=[data[8+ap+i:8+ap+i+40].split(b'\0')[0].decode() for i in range(0,asz,66)]
 ids=[v[0] for v in struct.iter_unpack('<Q',data[8+ip:8+ip+isz])];entries=[]
 for i,aid in enumerate(ids):
  size,ai,off,header=struct.unpack_from('<IIIi',data,8+mp+16*i)
  if 'mods' in archives[ai].lower():entries.append({'id':f'{aid:016X}','archive':archives[ai],'size':size,'offset':off,'header':header})
 print(json.dumps({'path':str(path),'size':len(data),'sha1':hashlib.sha1(data).hexdigest(),'sha256':hashlib.sha256(data).hexdigest(),'assets':len(ids),'archives':len(archives),'mod_entries':entries},indent=2))
b=Path(r'C:\Program Files (x86)\Steam\depotcache\1895881_2186341403927512776.manifest').read_bytes();p=b.find(b'toc');print('Manifest header',b[:20].hex(),'toc offset',p,'context',b[p-16:p+128].hex())
