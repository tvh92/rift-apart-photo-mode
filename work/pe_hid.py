exec(open(r'work\pe_imports.py').read().replace("names(1); names(13,True)", ""))
rva,size=struct.unpack_from('<II',b,dd+8); pos=off(rva)
while True:
  oft,ts,fw,name_rva,iat=struct.unpack_from('<IIIII',b,pos)
  if not any((oft,ts,fw,name_rva,iat)): break
  n=off(name_rva);e=b.index(b'\0',n);dll=b[n:e].decode(errors='replace')
  if dll.lower()=='hid.dll':
    print('HID import entries:')
    thunk=off(oft or iat)
    while True:
      val=struct.unpack_from('<Q',b,thunk)[0]
      if not val:break
      if val>>63: print('ordinal',val&0xffff)
      else:
        q=off(val);h=struct.unpack_from('<H',b,q)[0];end=b.index(b'\0',q+2);print(b[q+2:end].decode(errors='replace'))
      thunk+=8
  pos+=20


