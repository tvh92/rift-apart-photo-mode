"""Preserve the exact user-confirmed build; do not install or change game files."""
import datetime,hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
folder=root/'outputs/camera-native-fog-candidate'
game=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart')
expected='228620169d5741cd57d544047d351e7bd3c7df541778bc78c17ea0655bcb6f2a'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(game/'hid.dll')==digest(folder/'hid.dll')==expected
confirmation={'user_message':'Confirmed to work','recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'dll_sha256':expected,'scope':'User confirmation in response to native startup/Photo fog/Ctrl/exit-reentry test request.'}
for name in ('build-verification.json','installation-audit.json'):
    path=folder/name; data=json.loads(path.read_text(encoding='utf-8-sig'))
    data['runtime_confirmation']=confirmation
    if name=='build-verification.json':data['runtime_status']='User-confirmed working native Photo fog build.'
    else:data['in_game_status']='User confirmed native fog test works; file audit passed before launch.'
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
snapshot=root/'outputs/confirmed-photo-fog/2026-10-05'
snapshot.mkdir(parents=True,exist_ok=True)
names=['hid.dll','CameraBoost.c','CameraStubs.S','GeometryLOD.h','PhotoLOD.h','PhotoFog.h',
       'HidExports.c','hid.def','export-manifest.json','build-verification.json','installation-audit.json','README.md']
for name in names:
    target=snapshot/name
    if target.exists():assert digest(target)==digest(folder/name),'Existing confirmed snapshot differs: '+name
    else:shutil.copy2(folder/name,target)
if (game/'PhotoModeCamera.log').exists():
    target=snapshot/'user-confirmed-runtime.log'
    if not target.exists():shutil.copy2(game/'PhotoModeCamera.log',target)
target=snapshot/'PhotoModeCamera.ini'
if not target.exists():shutil.copy2(game/'PhotoModeCamera.ini',target)
(root/'work/native-fog-confirmation.json').write_text(json.dumps(confirmation,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'confirmed_dll':expected,'snapshot':str(snapshot),'game_files_changed':False}))
