import runpy,struct
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py');rows=list(struct.iter_unpack('<3I',Path('work/rip-refs.bin').read_bytes()))
for off in [0x2e68730,0x2e688f8,0x2f135e0,0x3033f00,0x3034120,0x3034170]:
 for n,va,vs,rp,rs in r['SECTIONS']:
  if rp<=off<rp+rs:
   t=va+off-rp;print(hex(off),hex(t),[(hex(ip),hex(z)) for q,ip,z in rows if q==t]);break
