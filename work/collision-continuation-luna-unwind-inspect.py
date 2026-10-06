import runpy
r=runpy.run_path('work/disassemble_camera.py')
for a in [0x512adb8]:
 print(hex(a),r['bytes_at'](a,80).hex(' '),r['bytes_at'](a,80))
