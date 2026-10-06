import runpy,re,struct
r=runpy.run_path('work/disassemble_camera.py')
for m in re.finditer(rb'\.\?AV[^\x00]{0,160}Perf[^\x00]{0,160}\x00',r['DATA']):print(hex(m.start()),m.group()[:-1].decode())
refs=list(struct.iter_unpack('<3I',open('work/rip-refs.bin','rb').read()))
for target in [0x51ef9a0,0x2fbf630,0x45fd1e0]:
 print('TARGET',hex(target))
 for t,i,n in refs:
  if t==target:print(hex(i),r['bounds'](i))
