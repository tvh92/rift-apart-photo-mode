import struct
p=r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\RiftApart.exe'
b=open(p,'rb').read(); pe=struct.unpack_from('<I',b,0x3c)[0]; machine,nsec=struct.unpack_from('<HH',b,pe+4); optsz=struct.unpack_from('<H',b,pe+20)[0]; opt=pe+24; magic=struct.unpack_from('<H',b,opt)[0]; dd=opt+(112 if magic==0x20b else 96); secs=[]
for i in range(nsec):
 s=pe+24+optsz+40*i; name=b[s:s+8].split(b'\0')[0].decode(errors='replace'); vsize,rva,rawsize,raw=struct.unpack_from('<IIII',b,s+8); secs.append((name,rva,max(vsize,rawsize),raw,rawsize))
def off(r):
 for name,va,size,raw,rs in secs:
  if va<=r<va+size: return raw+r-va
 raise ValueError(hex(r))
def names(idx, delay=False):
 rva,size=struct.unpack_from('<II',b,dd+idx*8)
 print(('delay' if delay else 'import')+' directory',hex(rva),hex(size))
 if not rva:return
 pos=off(rva)
 while 1:
  if delay:
   d=struct.unpack_from('<8I',b,pos)
   if not any(d):break
   nameRva=d[1]
  else:
   d=struct.unpack_from('<IIIII',b,pos)
   if not any(d):break
   nameRva=d[3]
  i=off(nameRva); e=b.index(b'\0',i); print(b[i:e].decode(errors='replace'))
  pos+=32 if delay else 20
print('machine',hex(machine),'optional',hex(magic),'sections',nsec)
names(1); names(13,True)

