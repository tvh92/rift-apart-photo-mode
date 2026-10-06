"""Verify the narrow specular extension and preserved installed status/fog scope."""
import ast,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];folder=root/'outputs/camera-native-lighting-v2';prior=root/'outputs/camera-native-status-candidate'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
previous='77051506a589b1051556505b309c32eb7a4a69e93df93d0a29d85b74b045a2d0'
assert digest(prior/'hid.dll')==previous
unchanged=['CameraBoost.c','CameraStubs.S','GeometryLOD.h','HidExports.c','hid.def','export-manifest.json','PhotoFog.h','PhotoIndicator.h']
for name in unchanged:assert (folder/name).read_bytes()==(prior/name).read_bytes(),name
old=(prior/'PhotoLight.h').read_text()
old=old.replace('"\\x81\\xe2\\xff\\xff\\xfb\\xff",6);p+=6; /* clear local far-RGB bit18 */',
                '"\\x81\\xe2\\xff\\xff\\xeb\\xff",6);p+=6; /* clear local far-RGB bit18 and far-specular bit20 */')
assert old==(folder/'PhotoLight.h').read_text(),'Unexpected ordinary light scope change'
tree=ast.parse((root/'work/verify_fog_candidate.py').read_text())
parser=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='imports')
scope={};exec('import struct',scope);exec(compile(ast.Module(body=[parser],type_ignores=[]),'PE_import_parser','exec'),scope)
dependencies=scope['imports'](folder/'hid.dll');assert dependencies==scope['imports'](prior/'hid.dll')
log=(root/'work/specular-candidate-build-test.log').read_text()
markers=['1920 arithmetic cases','all 29 relay instruction starts unwind','24 native fade cases',
 'near fade/source preservation','adjacent-byte preservation','prior RGB-only override specular=0/type=1; new specular=0.7/type=0',
 'Type4 specular example at85: native=0.5; retained=1','PhotoFogProbe passed','dormant startup UI',
 'owner filtering, normal/Shift/release speeds','GDI resource cleanup','notifications stay dormant until validated lazy start',
 '"all_exports_resolved": 44']
for marker in markers:assert marker in log,marker
manifest={'game_sha256':'51299faca61866cf10ea9035a15b8f22600a56557dd5ffc1aad390d5a54e6d82',
 'dll_sha256':digest(folder/'hid.dll'),'previous_dll_sha256':previous,'installed':False,
 'runtime_status':'Native diffuse/specular/type4 probes pass; in-game lighting comparison pending.',
 'user_ui_test_waived':True,'unchanged_sources':unchanged,'dependencies':dependencies,
 'source_hashes':{p.name:digest(p) for p in folder.iterdir() if p.suffix in ('.c','.h','.S','.def')},
 'new_behaviour':'Ordinary helper clears local far-colour bit18 and far-specular bit20, retaining source intensity/type at distance. Type4 helper clears far bit18 in private B0-byte prefix; original once, near fade/source unchanged.',
 'native_sites':['1099270: existing aligned8 mid-function leaf relay/registered CHAININFO','10BE260: aligned8 word changes only CALL10BE261 displacement; adjacent3 bytes preserved'],
 'isolated_tests':markers,'review':'work/photo-specular-actual-source-review.txt',
 'limitations':'Separate clip-volume eligibility, hierarchy/resource visibility, loaded-light availability, attenuation radius and shader light capacity remain native. Complete prevention of light disappearance unconfirmed.'}
(folder/'build-verification.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'dll_sha256':manifest['dll_sha256'],'dependencies':dependencies,'preserved_sources':unchanged,'tests_passed':True},indent=2))
