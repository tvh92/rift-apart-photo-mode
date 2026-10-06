import runpy,struct
r=runpy.run_path('work/disassemble_camera.py')
for s,e in [(0x456c1f0,0x456c280),(0x457aae0,0x457ab20)]:
 print('RANGE',hex(s))
 for p in range(s,e,8):
  v=struct.unpack('<Q',r['bytes_at'](p,8))[0]; print(hex(p),hex(v),hex(v-r['BASE']) if r['BASE']<=v<r['BASE']+0x7155000 else '')
