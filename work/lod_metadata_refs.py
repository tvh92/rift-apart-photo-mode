import struct,json
from pathlib import Path
p=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\RiftApart.exe');d=p.read_bytes()
pe=struct.unpack_from('<I',d,0x3c)[0];ns=struct.unpack_from('<H',d,pe+6)[0];os=struct.unpack_from('<H',d,pe+20)[0];base=struct.unpack_from('<Q',d,pe+48)[0]
sections=[]
for i in range(ns):
 p=pe+24+os+40*i;vs,va,rs,rp=struct.unpack_from('<4I',d,p+8);sections.append((va,vs,rp,rs))
def rva(off):
 for va,vs,rp,rs in sections:
  if rp<=off<rp+rs:return va+off-rp
 raise ValueError(hex(off))
for s in [b'LodScaleMultiplier\0',b'ModelLodClamp\0',b'CamLodScale\0',b'This specifies the LOD scale multiplier (it is applied globally).\0']:
 pos=d.index(s);target=base+rva(pos);pattern=struct.pack('<Q',target);refs=[];j=d.find(pattern)
 while j>=0:
  refs.append(hex(rva(j)));j=d.find(pattern,j+1)
 print(s.decode().rstrip('\0'),'RVA',hex(rva(pos)),'pointer references',refs)
