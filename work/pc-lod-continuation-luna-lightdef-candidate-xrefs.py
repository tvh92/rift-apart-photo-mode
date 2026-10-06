import runpy,struct
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py')
rows=list(struct.iter_unpack('<3I',Path('work/branch-refs.bin').read_bytes()))
for target in [0x1A6C201,0x1A6C2C7,0x1A6C3CA,0x163BB50,0x1A6C740]:
 hits=[(ip,n) for t,ip,n in rows if t==target]
 print('TARGET',hex(target),'xrefs',[(hex(ip),tuple(hex(x) for x in r['bounds'](ip))) for ip,n in hits])
 for ip,n in hits:
  for a,line in r['disassemble'](ip):
   if a==ip: print(' ',hex(a),line)
