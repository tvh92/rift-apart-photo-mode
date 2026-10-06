import runpy
r=runpy.run_path('work/disassemble_camera.py')
for a,n in [(0x1A5F1E7,0x22),(0x1A5F146,0x70),(0x1A5F234,0xD0)]: print(hex(a),r['bytes_at'](a,n).hex(' '))
print('bounds',tuple(hex(x) for x in r['bounds'](0x1A5F1EE)))
