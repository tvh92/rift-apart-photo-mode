import re
from pathlib import Path
p=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\RiftApart.exe');d=p.read_bytes()
patterns=[b'BootSequence_PC.movie',b'bootsequence_pc',b'skipintro',b'skip_intro',b'nointro',b'noboot',b'nomovie',b'nosplash',b'splash',b'BootSequence',b'SkipIntro',b'boot movie']
out=Path('work/intro-native/exe_boot_strings.txt')
with out.open('w',encoding='utf-8') as f:
 for pat in patterns:
  hits=[];i=0
  while True:
   i=d.lower().find(pat.lower(),i)
   if i<0:break
   lo=max(0,i-80);hi=min(len(d),i+len(pat)+100)
   hits.append((i,d[lo:hi]))
   i+=1
  f.write(f'{pat.decode()}: {len(hits)} matches\n')
  for off,ctx in hits[:20]:f.write(f'  {off:#x}: {ctx!r}\n')
 # general printable strings mentioning candidate tokens, narrow lengths
 for kind,rx,unit in [('ascii',re.compile(rb'[ -~]{5,}'),1),('utf16le',re.compile(rb'(?:[ -~]\x00){5,}'),2)]:
  f.write(f'\n{kind} matching strings:\n')
  for m in rx.finditer(d):
   s=m.group().decode('ascii' if unit==1 else 'utf-16le','ignore')
   if re.search(r'boot|skip.?intro|no.?intro|no.?movie|no.?splash|startup.?movie|movie.?boot',s,re.I):f.write(f'  {m.start():#x}: {s}\n')
print(out.resolve())
