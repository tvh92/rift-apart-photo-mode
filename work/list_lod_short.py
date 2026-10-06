import json
from pathlib import Path
rows=json.loads(Path('work/lod-strings.json').read_text())
for row in rows:
 s=row['string']
 if 'Lod' in s or 'LOD' in s:
  if len(s)<95:print(row['file_offset'],s)

