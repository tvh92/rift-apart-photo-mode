import struct,runpy
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py')
rows=list(struct.iter_unpack('<3I',Path('work/branch-refs.bin').read_bytes()))
for target in [0x1a5ab40,0x1a56d70,0x1a57560]:
 print('\nTARGET',hex(target))
 for _,ip,n in [x for x in rows if x[0]==target]:
  print('\nCALLSITE',hex(ip),'owner',tuple(hex(a) for a in r['bounds'](ip)))
  inst=r['disassemble'](ip); idx=next((i for i,(a,s) in enumerate(inst) if a==ip),-1)
  for a,s in inst[max(0,idx-6):idx+2]:print(f'{a:08x} {s}')
