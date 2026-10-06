import runpy,struct,time
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py');Decoder=r['Decoder'];refs=[];t=time.monotonic()
for name,va,vs,rp,rs in r['SECTIONS']:
 if name!=b'.text':continue
 for instruction in Decoder(64,r['DATA'][rp:rp+rs],ip=va):
  if instruction.is_ip_rel_memory_operand:
   target=instruction.ip_rel_memory_address
   if 0<=target<0x80000000:refs.append((target,instruction.ip,instruction.len))
refs.sort()
with Path('work/rip-refs.bin').open('wb') as f:
 for row in refs:f.write(struct.pack('<3I',*row))
print('Indexed',len(refs),'RIP-relative instructions in',round(time.monotonic()-t,2),'seconds.')
