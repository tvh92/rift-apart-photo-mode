import re,json
from pathlib import Path
p=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\RiftApart.exe')
d=p.read_bytes();records=[]
for m in re.finditer(rb'[ -~]{5,}',d):
 s=m.group().decode()
 if re.search(r'LOD|Lod|lod_|_lod|lodBias|[Cc]ull|[Dd]etail',s) and not re.search(r'Explod|explod|Implod|implod',s):
  records.append({'file_offset':hex(m.start()),'string':s})
Path('work/lod-strings.json').write_text(json.dumps(records,indent=2))
print('Matching strings:',len(records))
for record in records:
 if not record['string'].startswith('.?A') and len(record['string'])<180:print(record['file_offset'],record['string'])
