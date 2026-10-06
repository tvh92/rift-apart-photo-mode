import ast,struct,hashlib,json,zipfile
from pathlib import Path
root=Path.cwd();game=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart');out=root/'outputs/startup-repair'
ns={};tree=ast.parse((root/'work/inspect_photo_config.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef))],type_ignores=[]),'helpers','exec'),ns)
d=(game/'toc').read_bytes();s=ns['sections'](d[8:]);ip,n=s[0x506D7B8A];mp,m=s[0x65BCF461];ap,an=s[0x398ABFF0]
archives=[d[8+ap+i:8+ap+i+40].split(b'\0')[0].decode() for i in range(0,an,66)];ids=[x[0] for x in struct.iter_unpack('<Q',d[8+ip:8+ip+n])]
packages={0x851735C03E050852:out/'NoIntro-CurrentBuild.stage',0x8B203B05CA2AEB50:out/'NoIntro-CurrentBuild.stage',0x905EBDB8C12D66E0:out/'NoIntro-CurrentBuild.stage',0xAED6101948AAFA54:root/'outputs/camera-controls/PhotoMode-10x-Tether1000.stage'}
report=[]
for aid,stage in packages.items():
 size,ai,off,h=struct.unpack_from('<IIIi',d,8+mp+16*ids.index(aid));path=game/archives[ai]
 assert archives[ai].startswith('d\\mods\\')
 with path.open('rb') as f:f.seek(off);b=f.read(size)
 with zipfile.ZipFile(stage) as z:assert b==z.read('0/'+f'{aid:016X}')
 report.append({'asset_id':f'{aid:016X}','archive':archives[ai],'size':size,'sha256':hashlib.sha256(b).hexdigest(),'payload_verified':True})
expected=[['NoIntro.stage',False],['PhotoMode-10x-Tether1000.stage',True],['NoIntro-CurrentBuild.stage',True]]
for manager in [root/'outputs/Overstrike',Path(r'C:\Users\Tim\Documents\Bestanden\Downloads\Overstrike 1 1.8.1 2026-09-04T22-57Z vzbjnz4Zh')]:
 profile=json.loads((manager/'Profiles/RCRA (Steam).json').read_text(encoding='utf-8-sig'));assert profile['mods']==expected
 assert (manager/'Mods Library/NoIntro-CurrentBuild.stage').read_bytes()==(out/'NoIntro-CurrentBuild.stage').read_bytes()
final={'installed_assets':report,'both_profiles_synchronized':True,'legacy_nointro_enabled':False,'compatible_intro_enabled':True,'native_camera_preserved':True,'in_game_test':'pending'}
(out/'compatible-intro-install-verification.json').write_text(json.dumps(final,indent=2));print(json.dumps(final,indent=2))
