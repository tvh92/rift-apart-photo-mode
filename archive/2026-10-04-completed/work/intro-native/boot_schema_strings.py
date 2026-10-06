import re
from pathlib import Path
d=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\RiftApart.exe').read_bytes()
for lo,hi in [(0x2e687c0,0x2e68a40)]:
 for m in re.finditer(rb'[ -~]{3,}',d[lo:hi]):print(hex(lo+m.start()),m.group().decode('ascii','replace'))
