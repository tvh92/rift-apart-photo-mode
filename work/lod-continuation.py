import runpy, struct, sys, bisect
from pathlib import Path
r = runpy.run_path('work/disassemble_camera.py')
rows = list(struct.iter_unpack('<III', Path('work/rip-refs.bin').read_bytes()))
targets = [x[0] for x in rows]
for arg in sys.argv[1:]:
    if arg.startswith('s:'):
        p = r['DATA'].find(arg[2:].encode()+b'\0')
        if p < 0:
            print('NOT FOUND', arg); continue
        target = next(va+p-rp for name,va,vs,rp,rs in r['SECTIONS'] if rp<=p<rp+rs)
    else: target = int(arg,0)
    hits = rows[bisect.bisect_left(targets,target):bisect.bisect_right(targets,target)]
    print('TARGET',arg,hex(target),'REFS',len(hits))
    for t,ip,n in hits:
        b,e = r['bounds'](ip)
        print('REF',hex(ip),'FUNCTION',hex(b),hex(e))
        lines = r['disassemble'](ip)
        k = next((i for i,v in enumerate(lines) if v[0]==ip),0)
        for a,l in lines[max(0,k-8):k+12]: print(f'{a:08x} {l}')
