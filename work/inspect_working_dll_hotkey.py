from pathlib import Path
import sys, struct
sys.path.insert(0,str(Path('work/disasm').resolve()))
from iced_x86 import Decoder, Formatter, FormatterSyntax

p=Path('outputs/camera-native/backup/2026-10-05-before-control-indicator/hid.dll')
d=p.read_bytes();pe=struct.unpack_from('<I',d,0x3c)[0];ns,osz=struct.unpack_from('<H',d,pe+6)[0],struct.unpack_from('<H',d,pe+20)[0]
base=struct.unpack_from('<Q',d,pe+48)[0]
secs=[]
for n in range(ns):
    s=pe+24+osz+40*n;vsize,va,size,pos=struct.unpack_from('<4I',d,s+8)
    secs.append((d[s:s+8].split(b'\0')[0],va,pos,size))
fmt=Formatter(FormatterSyntax.NASM)
for name,va,pos,size in secs:
    if name!=b'.text':continue
    hits=[];start=pos
    while True:
        at=d.find(b'\xb9\x4c\x00\x00\x00',start,pos+size)
        if at<0:break
        hits.append(at);start=at+1
    print('L-key-immediate sites:',[hex(x) for x in hits])
    for at in hits:
        start=max(pos,at-96);end=at+200
        for i in Decoder(64,d[start:end],ip=va+start-pos):print(f'{i.ip:08x}: {fmt.format(i)}')
