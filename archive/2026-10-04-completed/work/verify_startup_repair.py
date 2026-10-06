import ast,struct,hashlib,json,zipfile
from pathlib import Path
root=Path.cwd();game=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart');repair=root/'outputs/startup-repair'
ns={};tree=ast.parse((root/'work/inspect_photo_config.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef))],type_ignores=[]),'helpers','exec'),ns)
def table(path):
 data=path.read_bytes();s=ns['sections'](data[8:]);ap,asz=s[0x398ABFF0];ip,isz=s[0x506D7B8A];mp,msz=s[0x65BCF461];sp,ssz=s[0xEDE8ADA9]
 archives=[data[8+ap+i:8+ap+i+40].split(b'\0')[0].decode() for i in range(0,asz,66)]
 ids=[v[0] for v in struct.iter_unpack('<Q',data[8+ip:8+ip+isz])]
 rows=list(struct.iter_unpack('<IIIi',data[8+mp:8+mp+msz]));return data,s,archives,ids,rows,data[8+sp:8+sp+ssz]
clean=table(repair/'toc.steam-original');installed=table(game/'toc');ref=json.loads((repair/'steam-toc-reference.json').read_text())
assert hashlib.sha1(clean[0]).hexdigest()==ref['sha1'];assert hashlib.sha1((game/'toc.BAK').read_bytes()).hexdigest()==ref['sha1']
assert clean[3]==installed[3];assert clean[5]==installed[5];assert installed[2][:len(clean[2])]==clean[2]
expected={0x851735C03E050852,0x8B203B05CA2AEB50,0x905EBDB8C12D66E0,0xAED6101948AAFA54}
changed=[];relocated_headers=[]
for i,aid in enumerate(clean[3]):
 a,b=clean[4][i],installed[4][i]
 if a[:3]!=b[:3]:changed.append(f'{aid:016X}');assert aid in expected,(hex(aid),a,b)
 elif a[3]!=b[3]:relocated_headers.append(f'{aid:016X}')
assert set(int(a,16) for a in changed)==expected
assert not relocated_headers,relocated_headers[:5]
assert hashlib.sha256((game/'hid.dll').read_bytes()).hexdigest()=='97b9a29eed154973fb587e0fae965c441b9956096211523aa1f99ef1d6d03e81'
assert hashlib.sha256((game/'d/config').read_bytes()).hexdigest()=='f659e13afe36c335d3ab54441898378164a51c2c469a1a368a51c8a005310bb3'
report={'steam_build':23987138,'original_toc_sha1':ref['sha1'],'clean_backup_verified':True,'asset_count':len(clean[3]),'only_changed_assets':changed,'other_asset_records_unchanged':True,'spans_unchanged':True,'original_archive_list_preserved':True,'camera_dll_unchanged':True,'base_config_vanilla':True,'in_game_startup_test':'pending'}
(repair/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
