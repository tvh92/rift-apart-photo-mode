import re
from pathlib import Path
d=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\RiftApart.exe').read_bytes()
for center in [0x4750320,0x4757448]:
 print('CENTER',hex(center))
 lo=center-0x200;hi=center+0x220
 for m in re.finditer(rb'[ -~]{4,}',d[lo:hi]): print(hex(lo+m.start()),m.group().decode('ascii','replace'))
