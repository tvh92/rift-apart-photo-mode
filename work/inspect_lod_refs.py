import runpy,struct
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py')
targets=[0x3137ea8,0x3137eb0,0x47ccd40,0x47cd340,0x47cd160,0x47f9a48,0x47f9df0,0x3137f48,0x3137f60]
rows=list(struct.iter_unpack('<3I',Path('work/rip-refs.bin').read_bytes()))
for target in targets:
 refs=[ip for t,ip,n in rows if target-32<=t<=target+32]
 print('TARGET',hex(target),'CODE REFS',[(hex(ip),tuple(hex(x) for x in r['bounds'](ip))) for ip in refs[:20]])
 print('DATA NEAR')
 for off in range(target-32,target+64,8):
  value=struct.unpack('<Q',r['bytes_at'](off,8))[0];label=''
  if r['BASE']<=value<r['BASE']+0x7155000:
   try:
    text=r['bytes_at'](value-r['BASE'],128).split(b'\0')[0]
    if text and all(32<=v<127 for v in text):label=text.decode()
   except ValueError:pass
  print(hex(off),hex(value),label)
