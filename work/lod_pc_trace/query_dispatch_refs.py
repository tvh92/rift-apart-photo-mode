import struct
from pathlib import Path
rows=list(struct.iter_unpack('<3I',Path('work/branch-refs.bin').read_bytes()))
for t in [0x1684860,0x1689ba0,0x1688150,0x168ad40,0x168a3e0,0x1689e50,0x168a3f0]:
 print(hex(t),[hex(ip) for x,ip,n in rows if x==t])
