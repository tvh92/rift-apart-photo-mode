import runpy,struct
r=runpy.run_path('work/disassemble_camera.py');d=r['DATA'];b=r['BASE'];target=b+0x8a7350;p=d.find(struct.pack('<Q',target))
def rva(p):
 for name,va,vs,rp,rs in r['SECTIONS']:
  if rp<=p<rp+rs:return va+p-rp
while p>=0:
 print('pointer',hex(rva(p)))
 for x in range(p-80,p+8,8):
  v=struct.unpack_from('<Q',d,x)[0]
  if b+0x4a00000<v<b+0x5000000:
   vals=struct.unpack('<6I',r['bytes_at'](v-b,24))
   if vals[0]==1:
    off=r['offset'](vals[3])+16;print('vtable',hex(rva(x+8)),'name',d[off:off+160].split(b'\0')[0]);print([hex(v) for v in r['vtable'](rva(x+8),30)])
 p=d.find(struct.pack('<Q',target),p+1)
for t,i,n in struct.iter_unpack('<3I',open('work/rip-refs.bin','rb').read()):
 if t in [0x61287D0,0x6128868,0x61287E0]:print('MOVIE',hex(t),hex(i),tuple(hex(v) for v in r['bounds'](i)))
