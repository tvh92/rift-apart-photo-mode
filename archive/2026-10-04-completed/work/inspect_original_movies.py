import ast,struct,zipfile
from pathlib import Path
ns={};tree=ast.parse(Path('work/inspect_photo_config.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef))],type_ignores=[]),'helpers','exec'),ns)
d=Path('outputs/startup-repair/toc.steam-original').read_bytes();s=ns['sections'](d[8:]);ip,n=s[0x506D7B8A];mp,m=s[0x65BCF461];ap,an=s[0x398ABFF0];archives=[d[8+ap+i:8+ap+i+40].split(b'\0')[0].decode() for i in range(0,an,66)];ids=[x[0] for x in struct.iter_unpack('<Q',d[8+ip:8+ip+n])]
for aid in [0x851735C03E050852,0x8B203B05CA2AEB50,0x905EBDB8C12D66E0]:
 i=ids.index(aid);size,ai,off,h=struct.unpack_from('<IIIi',d,8+mp+16*i);p=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart')/archives[ai]
 with p.open('rb') as f:f.seek(off);head=f.read(100)
 print(hex(aid),archives[ai],size,off,h,head.hex())
with zipfile.ZipFile('outputs/Overstrike/Mods Library/NoIntro.stage') as z:
 b=z.read('0/movies/boot/bootsequence_pc.movie');print('replacement',b[:100].hex(),struct.unpack_from('<24I',b))
