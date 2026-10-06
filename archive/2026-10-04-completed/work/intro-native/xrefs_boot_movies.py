import runpy,struct
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py'); d=r['DATA'];
for off in [0x2fb0b48,0x2fb0b70,0x2fb0b98,0x2fb0bc0]:
 for name,va,vs,rp,rs in r['SECTIONS']:
  if rp<=off<rp+rs:
   target=va+off-rp
   rows=list(struct.iter_unpack('<3I',Path('work/rip-refs.bin').read_bytes()))
   print(hex(off),name,hex(target),[(hex(ip),hex(n)) for t,ip,n in rows if t==target])
   break
