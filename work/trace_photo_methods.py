import runpy,json,struct
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py');tables=json.loads(Path('work/lod-photo-vtables.json').read_text())
lines=[]
for name in ['PhotomodeSystem','PhotomodeSystemShared']:
 for vt in tables[name][0]['vtables']:
  lines.append(name+' '+vt['vtable'])
  for slot,m in enumerate(vt['methods']):
   v=int(m,16)
   if v<0x800000:continue
   lines.append('\nSLOT '+str(slot)+' '+m)
   lines += [f'{addr:08x} {line}' for addr,line in r['disassemble'](v)]
Path('work/lod-photo-disassembly.txt').write_text('\n'.join(lines))
print('\n'.join(lines[:110]))
