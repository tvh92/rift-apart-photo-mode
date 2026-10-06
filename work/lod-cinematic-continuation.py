import runpy,struct,json
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py');d=r['DATA'];base=r['BASE']
def rva(off):
    return next(va+off-rp for name,va,vs,rp,rs in r['SECTIONS'] if rp<=off<rp+rs)
out=[]; methods=set()
for name in ['Cinematic2System','Cinematic2Manager','Cinematic2Component','Cinematic2HooksShared']:
    p=d.index(('.?AV'+name+'@@\0').encode())-16;td=rva(p);j=d.find(struct.pack('<I',td)); vts=[]
    while j>=0:
        c=j-12
        if c>=0:
            vals=struct.unpack_from('<6I',d,c)
            if vals[0]==1 and vals[5]==rva(c):
                col=rva(c);pos=d.find(struct.pack('<Q',base+col))
                while pos>=0:
                    vt=rva(pos)+8; ms=r['vtable'](vt,120);methods.update(ms)
                    vts.append((hex(vt),[hex(x) for x in ms]));pos=d.find(struct.pack('<Q',base+col),pos+1)
        j=d.find(struct.pack('<I',td),j+1)
    out.append((name,vts))
Path('work/lod-cinematic-continuation-vtables.json').write_text(json.dumps(out,indent=2))
with Path('work/lod-cinematic-continuation-disasm.txt').open('w') as f:
    for m in sorted(methods):
        f.write(f'FUNCTION {m:#x}\n')
        for a,l in r['disassemble'](m):f.write(f'{a:08x} {l}\n')
print('Methods',len(methods))
