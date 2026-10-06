import ast,hashlib,json,struct,zipfile
from pathlib import Path
root=Path(__file__).resolve().parent.parent
game=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart')
ns={};tree=ast.parse((root/'work/inspect_photo_config.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef))],type_ignores=[]),'helpers','exec'),ns)
toc=(game/'toc').read_bytes();tags=ns['sections'](toc[8:])
ip,isz=tags[0x506D7B8A];ids=[v[0] for v in struct.iter_unpack('<Q',toc[8+ip:8+ip+isz])]
ap,asz=tags[0x398ABFF0];blob=toc[8+ap:8+ap+asz]
archives=[blob[i:i+40].split(b'\0')[0].decode() for i in range(0,asz,66)]
mp,_=tags[0x65BCF461]
expected={'851735C03E050852':('NoIntro.stage','0/movies/boot/bootsequence_china.movie'),
          '8B203B05CA2AEB50':('NoIntro.stage','0/movies/boot/bootsequence_eu.movie'),
          '905EBDB8C12D66E0':('NoIntro.stage','0/movies/boot/bootsequence_pc.movie'),
          'AED6101948AAFA54':('PhotoMode-10x-Tether1000.stage','0/AED6101948AAFA54')}
results=[]
for aid,(stage,entry) in expected.items():
 indexes=[i for i,v in enumerate(ids) if v==int(aid,16)];assert len(indexes)==1
 size,ai,offset,header=struct.unpack_from('<IIIi',toc,8+mp+16*indexes[0])
 name=archives[ai];assert name.startswith('d\\mods\\'),name
 data=(game/Path(name.replace('\\','/'))).read_bytes()[offset:offset+size]
 with zipfile.ZipFile(root/'outputs/Overstrike/Mods Library'/stage) as z:assert data==z.read(entry),(aid,'payload mismatch')
 results.append({'asset_id':aid,'archive':name,'size':size,'sha256':hashlib.sha256(data).hexdigest()})
base_hash=hashlib.sha256((game/'d/config').read_bytes()).hexdigest()
assert base_hash=='f659e13afe36c335d3ab54441898378164a51c2c469a1a368a51c8a005310bb3'
report={'base_config':'vanilla','base_config_sha256':base_hash,'verified_assets':results,'installed_via_overstrike':True}
(root/'outputs/camera-controls/overstrike-install-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
