"""Verify narrow status source scope and real native/UI regression evidence."""
import ast,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
folder=root/'outputs/camera-native-status-candidate'
previous=root/'outputs/camera-native-lighting-candidate'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prior='fa3ced0a22083cfe0e9ee68c96e5bdda2c4d13c46f34346c79848693873356b6'
assert digest(previous/'hid.dll')==prior
unchanged=['CameraBoost.c','CameraStubs.S','GeometryLOD.h','HidExports.c','hid.def','export-manifest.json','PhotoFog.h','PhotoLight.h']
for name in unchanged:assert (folder/name).read_bytes()==(previous/name).read_bytes(),name
tree=ast.parse((root/'work/verify_fog_candidate.py').read_text())
parser=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='imports')
scope={};exec('import struct',scope);exec(compile(ast.Module(body=[parser],type_ignores=[]),'PE_import_parser','exec'),scope)
dependencies=scope['imports'](folder/'hid.dll')
assert set(dependencies)==set(scope['imports'](previous/'hid.dll'))|{'gdi32.dll'}
log=(root/'work/status-candidate-build-test.log').read_text()
markers=['1920 arithmetic cases','all 29 relay instruction starts unwind','PhotoFogProbe passed',
 'dormant startup UI','ON/OFF/Ctrl rising-edge/focus/held guards','owner filtering, normal/Shift/release speeds',
 'premultiplied transparency','GDI resource cleanup','notifications stay dormant until validated lazy start',
 '"all_exports_resolved": 44']
for text in markers:assert text in log,text
manifest={'game_sha256':'51299faca61866cf10ea9035a15b8f22600a56557dd5ffc1aad390d5a54e6d82',
 'dll_sha256':digest(folder/'hid.dll'),'previous_tested_dll_sha256':prior,
 'installed':False,'runtime_status':'Native/UI probes and preview pass; in-game indicator/startup check pending.',
 'unchanged_sources':unchanged,'dependencies':dependencies,
 'source_hashes':{p.name:digest(p) for p in folder.iterdir() if p.suffix in ('.c','.h','.S','.def')},
 'ui':'Detail override: ON/OFF; top centre, click-through/no activation,900ms hold plus700ms fade. Lazy worker only in validated active Photo.',
 'isolated_tests':markers,
 'native_unwind_probe':'Test real instruction boundaries; interior immediate bytes are not valid RIP states and can resemble fake epilogs.',
 'lighting_feedback':'Prior fa3 user reports a farther light disappearance distance; primary relay867005 applications logged. Full lighting fix unconfirmed.',
 'limitations':'Indicator visibility in exclusive fullscreen requires in-game check. Lighting hooks unchanged; remaining light visibility limits unresolved.',
 'review':'work/photo-status-actual-source-review.txt'}
(folder/'build-verification.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'dll_sha256':manifest['dll_sha256'],'dependencies':dependencies,'unchanged_sources':unchanged,'isolated_checks_passed':True},indent=2))
