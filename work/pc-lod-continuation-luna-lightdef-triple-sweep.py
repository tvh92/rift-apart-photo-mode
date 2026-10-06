import runpy,time
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py')
from iced_x86 import Decoder,Formatter,FormatterSyntax
want={0x22c,0x230,0x234,0x238,0x23c}; fmt=Formatter(FormatterSyntax.NASM)
rows=[]
for begin,end,_ in r['PDATA']:
 if not begin or end<=begin: continue
 try: dec=Decoder(64,r['bytes_at'](begin,end-begin),ip=begin)
 except Exception: continue
 hits=[]
 for i in dec:
  if i.memory_base and i.memory_displacement in want: hits.append((i.memory_displacement,i.ip,fmt.format(i)))
 offs={x[0] for x in hits}
 if {0x22c,0x230,0x234}.issubset(offs): rows.append((begin,end,hits))
with Path('work/pc-lod-continuation-luna-lightdef-triple-offset-candidates.txt').open('w',encoding='utf8') as f:
 f.write(f'Functions using all offsets 22C,230,234 (offset collisions are expected): {len(rows)}\n')
 for begin,end,hits in rows:
  f.write(f'\nFUNCTION {begin:08X}-{end:08X}\n')
  for d,ip,line in hits: f.write(f'{ip:08X} [{d:X}] {line}\n')
print('count',len(rows))
