import struct
from pathlib import Path
for name in ['work/rip-refs.bin','work/branch-refs.bin']:
 rows=list(struct.iter_unpack('<3I',Path(name).read_bytes()))
 for t in [0x456c1e0,0x456c1f0,0x456c230,0x456c280,0x457aa68,0x457ab00]:
  print(name,hex(t),[hex(ip) for x,ip,n in rows if x==t])
