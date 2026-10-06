import runpy
r=runpy.run_path('work/disassemble_camera.py')
for f in [0x1A56D9B,0x1A571E0,0x1A57203]:
 print('\nFUNCTION',hex(f))
 for a,s in r['disassemble'](f):
  if ' call ' in (' '+s.lower()) or s.startswith('jmp') or 'mov dword' in s.lower() or 'mov byte' in s.lower(): print(f'{a:08x} {s}')
