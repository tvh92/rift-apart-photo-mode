import runpy
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py');D,Decoder=r['DATA'],r['Decoder'];text=next(x for x in r['SECTIONS'] if x[0]==b'.text');_,va,vs,rp,rs=text
slots=(0x128,0x148,0x158,0x160,0x168,0x170)
hits=[]
for ins in Decoder(64,D[rp:rp+rs],ip=va):
 if ins.is_call_near_indirect and ins.memory_displacement in slots:
  b,e=r['bounds'](ins.ip);hits.append((ins.ip,ins.memory_displacement,b,e,str(ins)))
out=Path('work/lod_pc_trace/nxapp_vtable_callers.txt')
with out.open('w') as f:
 f.write(f'indirect vtable call hits: {len(hits)}\n')
 for ip,d,b,e,s in hits:f.write(f'{ip:#x} slot={d:#x} fn={b:#x}-{e:#x} {s}\n')
print(out.resolve(),'hits',len(hits))
