import struct
from pathlib import Path
rows=list(struct.iter_unpack('<3I',Path('work/branch-refs.bin').read_bytes()))
for t in [0x8a7350,0x10cb0f0,0x565f20,0x5bc4e0]: print(hex(t),[hex(ip) for x,ip,n in rows if x==t])
