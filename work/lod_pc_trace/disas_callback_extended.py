import runpy
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py'); Decoder,Formatter,FS=r['Decoder'],r['Formatter'],r['FormatterSyntax']
for start,n in [(0x122f000,0x500),(0x122f500,0x400)]:
 data=r['bytes_at'](start,n);fmt=Formatter(FS.NASM)
 p=Path(f'work/lod_pc_trace/callback_{start:x}.txt')
 with p.open('w') as f:
  for ins in Decoder(64,data,ip=start): f.write(f'{ins.ip:08x} {fmt.format(ins)}\n')
 print(p.resolve())
