import runpy,struct
r=runpy.run_path('work/disassemble_camera.py');base=r['BASE'];d=r['DATA']
for vt in [0x2fbf630,0x45fd1e0]:
 print('VT',hex(vt))
 for i in range(50):
  q=struct.unpack('<Q',r['bytes_at'](vt+8*i,8))[0]
  if not base<=q<base+0x8000000:break
  print(i,hex(q-base))
for t in [0x1a57370,0x1a56d70,0x1a57560]:
 b=struct.pack('<Q',base+t);p=0;hits=[]
 while True:
  p=d.find(b,p)
  if p<0:break
  hits.append(p);p+=1
 print('PTR',hex(t),[hex(x) for x in hits])
