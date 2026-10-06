import runpy,struct
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py');d=r['DATA'];base=r['BASE']
for vt in [0x45fdef0,0x45fd8b0]:
 print('VTABLE',hex(vt))
 print([(i,hex(struct.unpack('<Q',r['bytes_at'](vt+8*i,8))[0]-base)) for i in range(20)])
for target in [0x1a5eba0,0x1a5eb90,0x1a5eb70,0x1a5eb80,0x183e400]:
 va=base+target;b=struct.pack('<Q',va);hits=[];p=0
 while True:
  p=d.find(b,p)
  if p<0:break
  hits.append(p);p+=1
 print('PTR',hex(target),'file offsets',[hex(x) for x in hits])
rows=list(struct.iter_unpack('<3I',Path('work/branch-refs.bin').read_bytes()))
for target in [0x1a5eba0,0x1a5eb90,0x1a5eb70,0x1a5eb80,0x183e400]:
 hits=[(ip,n) for t,ip,n in rows if t==target]
 print('BRANCHREF',hex(target),[(hex(ip),n) for ip,n in hits])
 for ip,n in hits:
  fn=r['bounds'](ip)
  dec=next((i for i in r['disassemble'](ip) if i[0]==ip),None)
  print('  ',tuple(hex(x) for x in fn),dec)
