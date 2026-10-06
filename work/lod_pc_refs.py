import runpy,struct
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py');d=r['DATA'];rows=list(struct.iter_unpack('<3I',Path('work/rip-refs.bin').read_bytes()))
def rva(off):
 for name,va,vs,rp,rs in r['SECTIONS']:
  if rp<=off<rp+rs:return va+off-rp
 raise ValueError()
for string in [b'Changed level of detail.\0',b'Level of Detail: %s\0',b'LevelOfDetail\0',b'PCGraphicsSettings_LevelOfDetail\0',b'Cinematic2System::m_ModelLods\0']:
 target=rva(d.index(string));refs=[ip for t,ip,n in rows if t==target]
 print(string.decode().rstrip('\0'),'RVA',hex(target),'refs',[(hex(ip),tuple(hex(x) for x in r['bounds'](ip))) for ip in refs])
