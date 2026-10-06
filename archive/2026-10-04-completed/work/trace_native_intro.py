import runpy,struct,json
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py');d=r['DATA'];refs=list(struct.iter_unpack('<3I',Path('work/rip-refs.bin').read_bytes()))
def rva(p):
 for name,va,vs,rp,rs in r['SECTIONS']:
  if rp<=p<rp+rs:return va+p-rp
for name in [b'BootSequence',b'movies/Boot/BootSequence_PC.movie',b'movies/Boot/BootSequence_EU.movie',b'movies/Boot/BootSequence_China.movie']:
 off=d.find(name+b'\0');v=rva(off);print(name.decode(),hex(v))
 for t,i,n in refs:
  if t==v:print(hex(i),tuple(hex(x) for x in r['bounds'](i)))
