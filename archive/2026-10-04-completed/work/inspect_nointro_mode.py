from pathlib import Path
import re,zipfile,json
b=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\RiftApart.exe').read_bytes()
for m in re.finditer(rb'[ -~]{5,}',b):
 s=m.group()
 if any(k in s.lower() for k in [b'skipintro',b'skip_intro',b'nointro',b'bootsequence']):print(hex(m.start()),s.decode())
with zipfile.ZipFile('outputs/Overstrike/Mods Library/NoIntro.stage') as z:
 print(z.read('info.json').decode());print([(n,len(z.read(n))) for n in z.namelist()])
