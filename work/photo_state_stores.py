import runpy
r=runpy.run_path('work/disassemble_camera.py');f=r['Formatter'](r['FormatterSyntax'].NASM)
for lo,hi in [(0x8dc160,0x8e5000),(0x1a56b00,0x1a5c300)]:
 for ins in r['Decoder'](64,r['bytes_at'](lo,hi-lo),ip=lo):
  if ins.memory_displacement in [0x54,0x50] and (ins.mnemonic or True):
   txt=f.format(ins)
   if any(s in txt for s in ['mov byte','cmp byte','mov dword']):print(hex(ins.ip),txt)
