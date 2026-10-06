import json
from pathlib import Path
for row in json.loads(Path('work/overstrike-tree.json').read_text())['tree']:
 p=row['path']
 if 'toc' in p.lower() or 'archive' in p.lower():print(p)
