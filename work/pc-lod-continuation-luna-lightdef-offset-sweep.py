import runpy,struct,time
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py')
from iced_x86 import Decoder,Formatter,FormatterSyntax
want={0x22c,0x230,0x234,0x238,0x23c}
fmt=Formatter(FormatterSyntax.NASM); rows=[]; t=time.monotonic()
for begin,end,_ in r['PDATA']:
    if not begin or end<=begin: continue
    try: dec=Decoder(64,r['bytes_at'](begin,end-begin),ip=begin)
    except Exception: continue
    hits=[]
    for i in dec:
        if i.memory_base != 0 and i.memory_displacement in want:
            hits.append((i.ip,fmt.format(i)))
    if hits: rows.append((begin,end,hits))
with Path('work/pc-lod-continuation-luna-lightdef-offset-sweep.txt').open('w',encoding='utf8') as f:
    f.write('Functions with at least one memory operand at reflected LightDef fade offsets; ambiguous offsets may alias unrelated layouts.\n')
    f.write(f'Count: {len(rows)}; elapsed {time.monotonic()-t:.2f}s\n')
    for begin,end,hits in rows:
        f.write(f'\nFUNCTION {begin:08X}-{end:08X}\n')
        for ip,line in hits: f.write(f'{ip:08X} {line}\n')
print('functions',len(rows),'seconds',round(time.monotonic()-t,2))
