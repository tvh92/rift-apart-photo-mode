import struct,runpy
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py')
rows=list(struct.iter_unpack('<3I',Path('work/branch-refs.bin').read_bytes()))
for target in [0x1a56d70,0x1a57560,0x1a57370,0x1a57320,0x1a57340,0x8dfd50,0x8dfa70,0x8de720]:
 print('\nTARGET',hex(target))
 for _,ip,n in [x for x in rows if x[0]==target]:
  print('xref',hex(ip),'len',n,'owner',tuple(hex(a) for a in r['bounds'](ip)),'instr',next((s for a,s in r['disassemble'](ip) if a==ip),'?'))
