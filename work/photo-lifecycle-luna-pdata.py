import runpy
r=runpy.run_path('work/disassemble_camera.py')
for t in [0x1A56D70,0x1A57203,0x1A57560,0x8DE1D0,0x8DFB08]:
 print('\nTARGET',hex(t))
 for row in r['PDATA']:
  if row[0]<=t<row[1] or abs(row[0]-t)<0x100 or abs(row[1]-t)<0x100:print(tuple(hex(x) for x in row))
 print('bounds',tuple(hex(x) for x in r['bounds'](t)))
