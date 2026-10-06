import struct
from pathlib import Path
rows=list(struct.iter_unpack('<3I',Path('work/rip-refs.bin').read_bytes()))
for t in [0x6203e58,0x6203d60,0x6748918,0x61287a0,0x61287d0,0x2fb19e0]:
 print(hex(t),[(hex(ip),hex(n)) for q,ip,n in rows if q==t])
