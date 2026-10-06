import runpy,struct,json
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py');d=r['DATA'];base=r['BASE']
def rva(off):
 for name,va,vs,rp,rs in r['SECTIONS']:
  if rp<=off<rp+rs:return va+off-rp
 raise ValueError(hex(off))
results={}
for name in ['PhotomodeSystem','PhotomodeSystemShared','PhotomodeCameraManagerData']:
 marker=('.?AV'+name+'@@\0').encode();p=d.index(marker)-16;td=rva(p);refs=[];j=d.find(struct.pack('<I',td))
 while j>=0:
  c=j-12
  if c>=0:
   vals=struct.unpack_from('<6I',d,c)
   if vals[0]==1 and vals[5]==rva(c):
    col=rva(c);pos=d.find(struct.pack('<Q',base+col));tables=[]
    while pos>=0:
     vt=rva(pos)+8;tables.append({'vtable':hex(vt),'methods':[hex(x) for x in r['vtable'](vt,80)]});pos=d.find(struct.pack('<Q',base+col),pos+1)
    refs.append({'COL':hex(col),'object_offset':vals[1],'vtables':tables})
  j=d.find(struct.pack('<I',td),j+1)
 results[name]=refs
Path('work/lod-photo-vtables.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
refs=[]
from iced_x86 import OpKind
for name,va,vs,rp,rs in r['SECTIONS']:
 if name!=b'.text':continue
 for ins in r['Decoder'](64,d[rp:rp+rs],ip=va):
  if ins.op_count and ins.op0_kind in (OpKind.NEAR_BRANCH16,OpKind.NEAR_BRANCH32,OpKind.NEAR_BRANCH64):
   target=ins.near_branch_target
   if 0<=target<0x80000000:refs.append((target,ins.ip,ins.len))
refs.sort()
with Path('work/branch-refs.bin').open('wb') as f:
 for row in refs:f.write(struct.pack('<3I',*row))
print('Indexed',len(refs),'direct branches.')
