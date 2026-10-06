from pathlib import Path
import struct,sys
sys.path.insert(0,str(Path('work/disasm').resolve()))
from iced_x86 import Decoder,Formatter,FormatterSyntax
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
p=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\RiftApart.exe')
d=p.read_bytes(); pe=struct.unpack_from('<I',d,0x3c)[0]; ns=struct.unpack_from('<H',d,pe+6)[0]; osz=struct.unpack_from('<H',d,pe+20)[0]; base=struct.unpack_from('<Q',d,pe+48)[0]
secs=[]
for i in range(ns):
 q=pe+24+osz+40*i; name=d[q:q+8].split(b'\0')[0]; vs,va,rs,rp=struct.unpack_from('<4I',d,q+8);secs.append((name,va,vs,rp,rs))
def off(rva):
 for name,va,vs,rp,rs in secs:
  if va<=rva<va+rs:return rp+rva-va
 raise ValueError(hex(rva))
def is_rva(x):
 try:off(x);return True
 except ValueError:return False
def dataranges(): return [(va,va+rs) for name,va,vs,rp,rs in secs if name in (b'.rdata',b'.data')]
def find4(val):
 b=struct.pack('<I',val);return [x for a,z in dataranges() for x in range(a,z-3,4) if d[off(x):off(x)+4]==b]
def qword(rva):return struct.unpack_from('<Q',d,off(rva))[0]
def print_vtable(name,td):
 # Find ClassHierarchyDescriptor field pointing to td at +12.
 cands=[]
 for ref in find4(td):
  chd=ref-12
  if is_rva(chd):cands.append(chd)
 chds=sorted(set(cands));cols=[]
 for chd in chds:
  for ref in find4(chd):
   col=ref-16
   if is_rva(col):
    b=d[off(col):off(col)+24]
    try: sig,offset,cd,td2,chd2,selfr=struct.unpack('<6I',b)
    except:continue
    if td2==td and chd2==chd:cols.append(col)
 print('TYPE',name,'td_rva',hex(td),'CHDs',[hex(x) for x in chds],'COLs',[hex(x) for x in sorted(set(cols))])
 for col in sorted(set(cols)):
  vrefs=find4(col)
  for ref in vrefs:
   vt=ref+8
   if not is_rva(vt):continue
   funcs=[]
   for i in range(64):
    ptr=qword(vt+8*i)
    if not base<=ptr<base+0x8000000:break
    funcs.append(ptr-base)
   if funcs:
    print(' VTABLE',hex(vt),'functions',len(funcs),'entries',[(i,hex(x)) for i,x in enumerate(funcs)])

targets=['PerfSpecGetAction','PerfSpecConfigConfigAllocator','PerfSpecConfig','LODLimiter','PerfSpecData']
for target in targets:
 print('STRING',target)
 start=0;found=[]
 while True:
  i=d.find(target.encode(),start)
  if i<0:break
  # decoded string start search back to probable '?AV' sequence
  s=max(0,i-16); e=d.find(b'\0',i)
  found.append((i,d[s:e].decode('ascii','replace')));start=i+1
 for i,s in found[:40]:print(hex(i),s)
 # decorated RTTI names in d; use all strings with class fragments
 names=[]
 for i,s in found:
  st=d.rfind(b'.?A',max(0,i-128),i+1)
  if st>=0:
   en=d.find(b'\0',st); nm=d[st:en].decode('ascii','replace')
   if nm.startswith('.?AV') or nm.startswith('.?AU'): names.append((nm,st))
 for nm,pos in sorted(set(names)):
  td=off(pos)-16
  # candidate TD must have standard RVA and point to name.
  try:
   trva=next(va+pos-rp for _,va,vs,rp,rs in secs if rp<=pos<rp+rs)
   tdrva=trva-16
   print_vtable(nm,tdrva)
  except Exception as e:print('parse_error',e)



