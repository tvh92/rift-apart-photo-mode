import runpy
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py'); D,Decoder=r['DATA'],r['Decoder']; text=next(x for x in r['SECTIONS'] if x[0]==b'.text'); _,va,vs,rp,rs=text
hits=[]
for ins in Decoder(64,D[rp:rp+rs],ip=va):
 if ins.memory_displacement in (0xA48,0xA50,0xA58):
  b,e=r['bounds'](ins.ip);hits.append((ins.ip,ins.memory_displacement,b,e,ins))
out=Path('work/lod_pc_trace/nxapp_callback_slots_allrefs.txt')
with out.open('w') as f:
 f.write(f'instruction hits: {len(hits)}\n')
 for ip,d,b,e,ins in hits:f.write(f'{ip:#x} slot={d:#x} function={b:#x}-{e:#x} {ins}\n')
print(out.resolve(),len(hits))
