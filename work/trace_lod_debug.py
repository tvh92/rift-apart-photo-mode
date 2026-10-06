import runpy,struct,re
r=runpy.run_path('work/disassemble_camera.py');d=r['DATA'];refs=list(struct.iter_unpack('<3I',open('work/rip-refs.bin','rb').read()))
def rva(off):
 for name,va,vs,rp,rs in r['SECTIONS']:
  if rp<=off<rp+rs:return va+off-rp
for name in [b'PerfProfileLodMax',b'Far Lod Cache Move Req',b'Geom Lod Efficiency',b'Geom Lod Level',b'FarLodCaching',b'FarLodTransitionDist']:
 p=d.find(name+b'\0');v=rva(p);print(name.decode(),hex(v))
 for t,i,n in refs:
  if t==v:print(hex(i),tuple(hex(x) for x in r['bounds'](i)))
