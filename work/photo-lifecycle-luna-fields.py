import runpy
r=runpy.run_path('work/disassemble_camera.py')
for f in [0x8DE720,0x8DFD50,0x8DFA70,0x1A56D9B,0x1A571E0,0x1A57203]:
 print('\nFUNCTION',hex(f))
 for a,s in r['disassemble'](f):
  if any(x in s.lower() for x in ['+50h]','+54h]','+50h,','+54h,','[rdi+50','[rdi+54']):print(f'{a:08x} {s}')
