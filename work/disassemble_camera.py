from pathlib import Path
import struct,sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'disasm'))
from iced_x86 import Decoder,Formatter,FormatterSyntax

DATA=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\RiftApart.exe').read_bytes()
pe=struct.unpack_from('<I',DATA,0x3c)[0];ns=struct.unpack_from('<H',DATA,pe+6)[0];os=struct.unpack_from('<H',DATA,pe+20)[0]
BASE=struct.unpack_from('<Q',DATA,pe+48)[0];SECTIONS=[]
for i in range(ns):
 p=pe+24+os+40*i;vs,va,rs,rp=struct.unpack_from('<4I',DATA,p+8);SECTIONS.append((DATA[p:p+8].split(b'\0')[0],va,vs,rp,rs))
def offset(rva):
 for name,va,vs,rp,rs in SECTIONS:
  if va<=rva<va+rs:return rp+rva-va
 raise ValueError(hex(rva))
def bytes_at(rva,n):return DATA[offset(rva):offset(rva)+n]
pr,ps=struct.unpack_from('<II',DATA,pe+24+112+3*8)
PDATA=[struct.unpack_from('<III',DATA,offset(pr)+i) for i in range(0,ps,12)]
def bounds(rva):
 for begin,end,unwind in PDATA:
  if begin<=rva<end:return begin,end
 return rva,rva+128
def disassemble(rva):
 begin,end=bounds(rva);formatter=Formatter(FormatterSyntax.NASM)
 return [(i.ip,formatter.format(i)) for i in Decoder(64,bytes_at(begin,end-begin),ip=begin)]
def vtable(rva,n=80):
 out=[]
 for i in range(n):
  ptr=struct.unpack('<Q',bytes_at(rva+8*i,8))[0]
  if not BASE<=ptr<BASE+0x4500000:break
  out.append(ptr-BASE)
 return out
if __name__=='__main__':
 for arg in sys.argv[1:]:
  rva=int(arg,0);print('FUNCTION',hex(rva),'BOUNDS',tuple(hex(x) for x in bounds(rva)))
  for addr,line in disassemble(rva):print(f'{addr:08x}',line)
