import runpy,struct
r=runpy.run_path('work/disassemble_camera.py')
base=0x456c0d8
for i in range(32,56):
 v=struct.unpack('<Q',r['bytes_at'](base+i*8,8))[0]
 print(i,hex(v-r['BASE']))
