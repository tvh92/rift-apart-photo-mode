import ctypes as C,struct,json,zipfile
from pathlib import Path
root=Path.cwd();game=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart');folder=root/'work/short-intro'
# This is the Bink runtime already shipped with the verified Steam game.
bink=C.WinDLL(str(game/'bink2w64.dll'),winmode=0x1100)
bink.BinkOpen.argtypes=[C.c_char_p,C.c_uint32];bink.BinkOpen.restype=C.c_void_p
bink.BinkClose.argtypes=[C.c_void_p];bink.BinkClose.restype=None
bink.BinkGetError.argtypes=[];bink.BinkGetError.restype=C.c_char_p
bink.BinkDoFrame.argtypes=[C.c_void_p];bink.BinkDoFrame.restype=C.c_int
bink.BinkNextFrame.argtypes=[C.c_void_p];bink.BinkNextFrame.restype=None
report=[]
with zipfile.ZipFile(root/'outputs/Overstrike/Mods Library/NoIntro.stage') as z:
 (folder/'legacy.bk2').write_bytes(z.read('0/movies/boot/bootsequence_pc.movie'))
for path in sorted(folder.glob('*.bk2')):
 h=bink.BinkOpen(str(path).encode(),0)
 error=(bink.BinkGetError() or b'').decode(errors='replace')
 row={'file':path.name,'opened':bool(h),'error':error}
 if h:
  try:
   row['header']=list(struct.unpack('<7I',C.string_at(h,28)))
   count=row['header'][2];assert count==4
   results=[]
   for i in range(count):
    results.append(bink.BinkDoFrame(h))
    if i+1<count:bink.BinkNextFrame(h)
   row['decoded_frame_calls']=results
   row['final_frame_number']=struct.unpack('<I',C.string_at(h+12,4))[0]
   row['last_error']=(bink.BinkGetError() or b'').decode(errors='replace')
  finally:bink.BinkClose(h)
 report.append(row)
print(json.dumps(report,indent=2));(root/'outputs/startup-repair/bink-validation.json').write_text(json.dumps(report,indent=2))
assert all(x['opened'] and len(x.get('decoded_frame_calls',[]))==4 for x in report if x['file']!='legacy.bk2')
