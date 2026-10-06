import runpy,re
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py');D,Decoder=r['DATA'],r['Decoder'];text=next(x for x in r['SECTIONS'] if x[0]==b'.text');_,va,vs,rp,rs=text
insns=list(Decoder(64,D[rp:rp+rs],ip=va));fmt=r['Formatter'](r['FormatterSyntax'].NASM)
hits=[]
for i,ins in enumerate(insns):
 if ins.is_call_near_indirect and ins.memory_displacement in (0x160,0x168,0x170):
  prev=[]
  for p in insns[max(0,i-6):i]:
   s=fmt.format(p)
   if re.match(r'lea rdx,\[rel ',s):prev.append((p.ip,p.ip_rel_memory_address,s))
  if prev:hits.append((ins.ip,ins.memory_displacement,r['bounds'](ins.ip),prev))
out=Path('work/lod_pc_trace/nxapp_setter_registration_sites.txt')
with out.open('w') as f:
 f.write(f'candidate setter call sites with nearby lea rdx: {len(hits)}\n')
 for ip,d,b,prev in hits:
  f.write(f'\n{ip:#x} slot={d:#x} fn={tuple(hex(x) for x in b)}\n')
  for a,t,s in prev:f.write(f'  {a:#x} target={t:#x} {s}\n')
print(out.resolve(),'hits',len(hits))
