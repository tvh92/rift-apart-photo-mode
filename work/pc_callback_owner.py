import runpy,struct
r=runpy.run_path('work/disassemble_camera.py');d=r['DATA'];refs=list(struct.iter_unpack('<3I',open('work/rip-refs.bin','rb').read()))
for t,i,n in refs:
 if 0x456c000<=t<0x456c270:print(hex(t),hex(i),tuple(hex(x) for x in r['bounds'](i)))
for p in range(0x456c160,0x456c260,8):
 v=struct.unpack('<Q',r['bytes_at'](p,8))[0]
 print(hex(p),hex(v), 'function' if r['BASE']<=v<r['BASE']+0x2e00000 else '')
