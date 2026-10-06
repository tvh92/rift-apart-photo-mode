"""Retain the user's partial lighting result and the real closed-session log."""
from pathlib import Path
import datetime,hashlib,json,shutil
root=Path(__file__).resolve().parents[1]
game=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart')
folder=root/'outputs/camera-native-lighting-candidate'
expected='fa3ced0a22083cfe0e9ee68c96e5bdda2c4d13c46f34346c79848693873356b6'
assert hashlib.sha256((game/'hid.dll').read_bytes()).hexdigest()==expected
assert hashlib.sha256((folder/'hid.dll').read_bytes()).hexdigest()==expected
log=(game/'PhotoModeCamera.log').read_text()
assert 'Photo primary surface-light colour fade override installed' in log
assert 'Photo surface-light primary relay applications=867005.' in log
feedback={'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'dll_sha256':expected,
 'user_report':'I think it works, but lights turn off at a farther Y distance with Ctrl enabled than at native X distance.',
 'classification':'Partial improvement; complete prevention of light disappearance is NOT confirmed.',
 'runtime_evidence':'Startup/Photo activation and Ctrl toggles logged; primary light relay applications=867005 at teardown.',
 'next_request':'Restore a brief fading on/off status indicator; keep Ctrl shortcut and original movies.'}
(root/'work/native-light-feedback-2026-10-06.json').write_text(json.dumps(feedback,indent=2)+'\n')
manifest=json.loads((folder/'build-verification.json').read_text(encoding='utf-8-sig'))
manifest['runtime_status']=feedback['classification']
manifest['runtime_feedback']=feedback
(folder/'build-verification.json').write_text(json.dumps(manifest,indent=2)+'\n')
snapshot=root/'outputs/tested-photo-lighting/2026-10-06'
snapshot.mkdir(parents=True,exist_ok=True)
for p in folder.iterdir():
    if p.is_file() and (p.suffix in ('.c','.h','.S','.def','.dll','.md','.json','.ps1')):
        target=snapshot/p.name
        if target.exists():assert target.read_bytes()==p.read_bytes(),target
        else:shutil.copy2(p,target)
shutil.copy2(game/'PhotoModeCamera.log',snapshot/'PhotoModeCamera.log')
(snapshot/'runtime-feedback.json').write_text(json.dumps(feedback,indent=2)+'\n')
print('Recorded partial lighting result; exact tested DLL/source/log preserved.')
