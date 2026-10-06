import runpy,struct
r=runpy.run_path('work/disassemble_camera.py'); d=r['DATA']; base=r['BASE']
for target in [0x1A6C201,0x1A6A180,0x1A6C6A2,0x1A6C6E4,0x1A6C740]:
 pat=struct.pack('<Q',base+target); hits=[]; pos=0
 while True:
  pos=d.find(pat,pos)
  if pos<0: break
  hits.append(pos); pos+=1
 print(hex(target),[hex(x) for x in hits[:40]],'count',len(hits))
 for off in hits[:10]:
  try: rv=r['to_rva'](off)
  except Exception: continue
  print('  rva',hex(rv),'near',hex(rv-8),'qword',hex(struct.unpack('<Q',r['bytes_at'](rv-8,8))[0]))
