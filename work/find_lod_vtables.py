import runpy,struct,json
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py');d=r['DATA'];base=r['BASE']
def rva(off):
 for name,va,vs,rp,rs in r['SECTIONS']:
  if rp<=off<rp+rs:return va+off-rp
 raise ValueError()
results={}
for name in ['PerfSpecData','NxSettingsImpl@nx','NxRenderer','RendererBackend@renoir']:
 marker=('.?AV'+name+'@@\0').encode();p=d.index(marker)-16;td=rva(p);refs=[];j=d.find(struct.pack('<I',td))
 while j>=0:
  c=j-12
  if c>=0:
   vals=struct.unpack_from('<6I',d,c)
   if vals[0]==1 and vals[5]==rva(c):
    col=rva(c);pos=d.find(struct.pack('<Q',base+col));tables=[]
    while pos>=0:
     vt=rva(pos)+8;tables.append({'vtable':hex(vt),'methods':[hex(x) for x in r['vtable'](vt,25)]});pos=d.find(struct.pack('<Q',base+col),pos+1)
    refs.append({'COL':hex(col),'object_offset':vals[1],'vtables':tables})
  j=d.find(struct.pack('<I',td),j+1)
 results[name]=refs
Path('work/lod-native-vtables.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
