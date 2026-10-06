import struct
from pathlib import Path
rows=list(struct.iter_unpack('<3I',Path('work/branch-refs.bin').read_bytes()))
for t in [0x16d9c70,0x16d9f20,0x16da010,0x16da8c0,0x16de140,0x16dc259,0x168ad40]:
 print(hex(t),[hex(ip) for x,ip,n in rows if x==t])
