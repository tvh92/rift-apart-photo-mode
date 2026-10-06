import runpy,struct
r=runpy.run_path('work/disassemble_camera.py');refs=list(struct.iter_unpack('<3I',open('work/rip-refs.bin','rb').read()));targets=[0x533934c,0x53391b8,0x5339370,0x456c230,0x456c1f0]
for t in targets:
 print('TARGET',hex(t))
 for target,i,n in refs:
  if target==t:print(hex(i),tuple(hex(x) for x in r['bounds'](i)))
