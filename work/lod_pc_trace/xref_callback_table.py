import runpy,struct
r=runpy.run_path('work/disassemble_camera.py'); d=r['DATA']; base=r['BASE']
for rv in [0x456c1f0,0x456c230,0x457aa68]:
 for va in [rv,base+rv]:
  k=0; found=[]; p=struct.pack('<Q',va)
  while 1:
   k=d.find(p,k)
   if k<0:break
   for name,secva,vs,rp,rs in r['SECTIONS']:
    if rp<=k<rp+rs: found.append((hex(va),hex(secva+k-rp)));break
   k+=1
  print(hex(va),found[:100])
