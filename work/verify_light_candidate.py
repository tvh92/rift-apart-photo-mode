"""Record exact artifact scope, regression results and compatible dependencies."""
import ast,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
folder=root/'outputs/camera-native-lighting-candidate'
confirmed=root/'outputs/confirmed-photo-fog/2026-10-05'
expected='228620169d5741cd57d544047d351e7bd3c7df541778bc78c17ea0655bcb6f2a'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert digest(confirmed/'hid.dll')==expected
# Reuse only the pure PE dependency parser, avoiding the fog verifier's writes.
tree=ast.parse((root/'work/verify_fog_candidate.py').read_text())
parser=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='imports')
scope={};exec('import struct',scope);exec(compile(ast.Module(body=[parser],type_ignores=[]),'PE_import_parser','exec'),scope)
dependencies=scope['imports'](folder/'hid.dll')
assert dependencies==scope['imports'](confirmed/'hid.dll')
unchanged=['CameraBoost.c','CameraStubs.S','GeometryLOD.h','HidExports.c','hid.def','export-manifest.json','PhotoFog.h']
for name in unchanged:assert (folder/name).read_bytes()==(confirmed/name).read_bytes(),name
log=(root/'work/lighting-candidate-build-test.log').read_text()
for marker in ('1920 arithmetic cases','all relay bytes unwind','PhotoFogProbe passed',
               'baseline lifecycle/teardown/metadata guards','owner filtering, normal/Shift/release speeds',
               '"all_exports_resolved": 44'):assert marker in log,marker
manifest={'game_sha256':'51299faca61866cf10ea9035a15b8f22600a56557dd5ffc1aad390d5a54e6d82',
          'dll_sha256':digest(folder/'hid.dll'),'previous_confirmed_dll_sha256':expected,
          'installed':False,'runtime_status':'Isolated tests pass; lighting candidate awaiting user runtime comparison.',
          'unchanged_confirmed_sources':unchanged,'dependencies':dependencies,
          'source_hashes':{p.name:digest(p) for p in folder.iterdir() if p.suffix in ('.c','.h','.S','.def')},
          'native_patch':{'rva':'1099270','bytes':8,'source_flags_untouched':True,'local_flag_cleared':18,
                          'guards':'Exact build/window/calltargets/unwind fragment; published ready, Photo Ctrl gate, four callers, primary view.',
                          'unwind':'Registered nested CHAININFO; leaf relay, no extra frame. All relay-byte positions tested.'},
          'isolated_tests':['1920 native arithmetic cases across four callsites','immutable source light records',
                            'native near fade, debug multiplier, specular scalar and type preserved',
                            'Ctrl off, unpublished relay, auxiliary view, foreign caller, exact-window refusal, atomic restoration',
                            'nested-chain virtual unwind at every relay byte','confirmed fog ABI/cache/texture-tail regression',
                            'Photo lifecycle, Ctrl focus/rising edge and teardown','camera normal/Shift/no-clip/geometry restoration',
                            '44 HID exports/GUID forwarding and unsupported-process refusal'],
          'limitations':'Only ordinary types0..3 camera-distance colour fade. Type4 specular fade, light ranking/512-entry capacity, streaming, shadows and source light radii remain native. No in-game lighting result yet.',
          'review':'work/photo-light-actual-source-review.txt'}
(folder/'build-verification.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'dll_sha256':manifest['dll_sha256'],'dependencies':dependencies,'confirmed_sources_unchanged':unchanged,'tests_passed':True},indent=2))
