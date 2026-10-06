import runpy,struct
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py'); rows=list(struct.iter_unpack('<3I',Path('work/rip-refs.bin').read_bytes()))
for target in [0x457aa68]:
 for x,ip,n in rows:
  if x==target: print(hex(ip),tuple(hex(a) for a in r['bounds'](ip)))
