from pathlib import Path
import struct
p=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\RiftApart.exe')
d=p.read_bytes()
for label, needle in [('field-hash',struct.pack('<I',0x3b89fd7d)),('field-name',b'CamCollisRad'),('default-f32',struct.pack('<f',0.2))]:
 hits=[]; pos=0
 while True:
  pos=d.find(needle,pos)
  if pos<0: break
  hits.append(hex(pos));pos+=1
 print(label, hits[:100], 'count=',len(hits))
import runpy,struct
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py')
d=r['DATA']; rows=list(struct.iter_unpack('<3I',Path('work/rip-refs.bin').read_bytes()))
def rva(off):
 for name,va,vs,rp,rs in r['SECTIONS']:
  if rp<=off<rp+rs:return va+off-rp
for off in [0x3170508,0x31706d8]:
 target=rva(off)
 print('offset',hex(off),'rva',hex(target),'refs',[(hex(ip),tuple(hex(x) for x in r['bounds'](ip))) for t,ip,n in rows if t==target])
 print('context',d[off-32:off+96].hex())
