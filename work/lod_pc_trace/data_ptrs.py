import runpy,struct
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py'); d=r['DATA']; base=r['BASE']
for rva in [0x168ad40,0x168ad40+base,0x16d9c70+base,0x16d9f20+base]:
 p=struct.pack('<Q',rva); found=[]; k=0
 while True:
  k=d.find(p,k)
  if k<0:break
  # file offset -> RVA
  rv=None
  for name,va,vs,rp,rs in r['SECTIONS']:
   if rp<=k<rp+rs:rv=va+k-rp;break
  found.append((hex(k),hex(rv) if rv is not None else None))
  k+=1
 print(hex(rva),found[:100])
