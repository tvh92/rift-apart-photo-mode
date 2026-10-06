import runpy
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py');D,Decoder=r['DATA'],r['Decoder']; text=next(x for x in r['SECTIONS'] if x[0]==b'.text');_,va,vs,rp,rs=text
hits=[]
for ins in Decoder(64,D[rp:rp+rs],ip=va):
    if ins.is_call_near_indirect and ins.memory_displacement in (0xA48,0xA50,0xA58):
        b,e=r['bounds'](ins.ip);hits.append((ins.ip,ins.memory_displacement,b,e,ins))
out=Path('work/lod_pc_trace/nxapp_callback_slots.txt')
with out.open('w',encoding='utf-8') as f:
    f.write(f'indirect call hits: {len(hits)}\n\n')
    for ip,disp,b,e,ins in hits:
        f.write(f'{ip:#x} slot={disp:#x} function={b:#x}-{e:#x} ins={ins}\n')
    funcs=sorted(set((b,e) for _,_,b,e,_ in hits))
    f.write(f'\nBounded functions: {len(funcs)}\n')
    for b,e in funcs:
        f.write(f'\nFUNCTION {b:#x}-{e:#x}\n')
        for a,line in r['disassemble'](b):
            if b<=a<e: f.write(f'{a:08x} {line}\n')
print(out.resolve(), 'hits=',len(hits),'functions=',len(set((b,e) for _,_,b,e,_ in hits)))
