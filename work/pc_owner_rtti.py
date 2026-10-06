import runpy,struct
r=runpy.run_path('work/disassemble_camera.py');d=r['DATA']
for p in range(0x456c000,0x456c168,8):
 v=struct.unpack('<Q',r['bytes_at'](p,8))[0]
 if r['BASE']+0x4a00000<v<r['BASE']+0x5000000:
  vals=struct.unpack('<6I',r['bytes_at'](v-r['BASE'],24))
  print(hex(p),vals)
  if vals[0]==1:
   off=r['offset'](vals[3])+16;print(d[off:off+200].split(b'\0')[0])
