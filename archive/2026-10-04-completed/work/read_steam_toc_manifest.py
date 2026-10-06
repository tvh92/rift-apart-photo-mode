import struct,json,hashlib
from pathlib import Path
manifest=Path(r'C:\Program Files (x86)\Steam\depotcache\1895881_2186341403927512776.manifest').read_bytes()
def vint(b,p):
 n=0;s=0
 while True:
  x=b[p];p+=1;n|=(x&127)<<s
  if not x&128:return n,p
  s+=7
  assert s<=70

def fields(b):
 p=0
 while p<len(b):
  tag,p=vint(b,p);wire=tag&7;num=tag>>3
  if wire==0:val,p=vint(b,p)
  elif wire==2:n,p=vint(b,p);val=b[p:p+n];p+=n
  elif wire==5:val=b[p:p+4];p+=4
  elif wire==1:val=b[p:p+8];p+=8
  else:raise ValueError(wire)
  yield num,val
magic,n=struct.unpack_from('<II',manifest);assert magic==0x71f617d0
files=[]
for tag,b in fields(manifest[8:8+n]):
 if tag!=1:continue
 f=dict(fields(b));name=f[1].decode()
 if name=='toc':
  row={'path':name,'size':f[2],'sha1':f[5].hex(),'manifest':'2186341403927512776','depot':1895881};files.append(row)
assert len(files)==1
Path('outputs/startup-repair/steam-toc-reference.json').write_text(json.dumps(files[0],indent=2));print(json.dumps(files[0],indent=2))
