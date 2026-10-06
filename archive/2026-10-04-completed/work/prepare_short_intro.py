import ast,struct,hashlib,zipfile,json
from pathlib import Path
root=Path.cwd();game=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart');out=root/'outputs/startup-repair';scratch=root/'work/short-intro';scratch.mkdir(exist_ok=True)
ns={};tree=ast.parse((root/'work/inspect_photo_config.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef))],type_ignores=[]),'helpers','exec'),ns)
d=(out/'toc.steam-original').read_bytes();assert hashlib.sha1(d).hexdigest()=='64946f571579d9ea0a17e675682e2994dc0f20fc'
s=ns['sections'](d[8:]);ip,n=s[0x506D7B8A];mp,m=s[0x65BCF461];ap,an=s[0x398ABFF0];archives=[d[8+ap+i:8+ap+i+40].split(b'\0')[0].decode() for i in range(0,an,66)];ids=[x[0] for x in struct.iter_unpack('<Q',d[8+ip:8+ip+n])]
report=[];payloads={}
for aid in [0x851735C03E050852,0x8B203B05CA2AEB50,0x905EBDB8C12D66E0]:
 size,ai,off,h=struct.unpack_from('<IIIi',d,8+mp+16*ids.index(aid));assert h==-1
 with (game/archives[ai]).open('rb') as f:f.seek(off);b=f.read(size)
 assert b[:4]==b'KB2j' and len(b)==size and struct.unpack_from('<I',b,4)[0]+8==size
 old_frames=struct.unpack_from('<I',b,8)[0];tracks=struct.unpack_from('<I',b,40)[0];assert tracks==2
 index=48+12*tracks;old_offsets=list(struct.unpack_from('<'+str(old_frames+1)+'I',b,index));assert (old_offsets[0]&~1)==index+4*(old_frames+1)
 keep=4;delta=4*(old_frames-keep);stop=old_offsets[keep]&~1;first=old_offsets[0]&~1
 head=bytearray(b[:index]);new_offsets=[x-delta for x in old_offsets[:keep+1]]
 clipped=head+struct.pack('<5I',*new_offsets)+b[first:stop]
 lengths=[(old_offsets[j+1]&~1)-(old_offsets[j]&~1) for j in range(keep)]
 struct.pack_into('<4I',clipped,4,len(clipped)-8,keep,max(lengths),keep)
 assert len(clipped)==(new_offsets[-1]&~1);assert (new_offsets[0]&1)==1
 # Payloads and all codec/audio metadata remain byte-identical to source.
 assert clipped[:4]==b[:4] and clipped[20:index]==b[20:index] and clipped[new_offsets[0]&~1:]==b[first:stop]
 for j in range(keep):
  start=new_offsets[j]&~1;end=new_offsets[j+1]&~1;pos=start
  for t in range(tracks):
   count=struct.unpack_from('<I',clipped,pos)[0];pos+=4+count;assert pos<=end
  assert pos<end
 name=f'{aid:016X}.bk2';(scratch/name).write_bytes(clipped);payloads[aid]=bytes(clipped)
 report.append({'asset_id':f'{aid:016X}','source_frames':old_frames,'frames':keep,'seconds':keep*struct.unpack_from('<I',b,32)[0]/struct.unpack_from('<I',b,28)[0],'audio_tracks':tracks,'bytes':len(clipped),'sha256':hashlib.sha256(clipped).hexdigest(),'original_codec_and_audio_metadata_preserved':True,'original_frame_packets_preserved':True})
stage=out/'NoIntro-CurrentBuild.stage'
with zipfile.ZipFile(stage,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 z.writestr('info.json',json.dumps({'game':'RCRA','format_version':2,'name':'Short intro (current-build compatible)','author':'Local compatibility patch','description':'Four initial frames from the locally installed game intro, preserving codec flags and audio tracks.'},indent=2))
 for aid,b in payloads.items():z.writestr('0/'+f'{aid:016X}',b)
(out/'short-intro-preparation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
