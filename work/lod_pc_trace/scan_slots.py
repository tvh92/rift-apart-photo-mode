import runpy, struct
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py'); D=r['DATA'];Decoder=r['Decoder']; text=next(x for x in r['SECTIONS'] if x[0]==b'.text');_,va,vs,rp,rs=text
found=[]
for ins in Decoder(64,D[rp:rp+rs],ip=va):
    if ins.is_call_near_indirect and ins.memory_displacement in (0x98,0xa0):
        found.append((ins.ip,ins.memory_displacement))
out=Path('work/lod_pc_trace/nxsettings_slot_callers.txt')
with out.open('w') as f:
 for ip,d in found:
  b,e=r['bounds'](ip);f.write(f'{ip:#x} slot {d:#x} function {b:#x}-{e:#x}\n')
  for a,line in r['disassemble'](ip):
   if b<=a<e: f.write(f'{a:08x} {line}\n')
  f.write('\n')
print(out.resolve(), 'hits',len(found))
