"""Record candidate tests, exact source scope, dependencies, and runtime limits."""
import hashlib,json,struct
from pathlib import Path
root=Path(__file__).resolve().parents[1]
folder=root/'outputs/camera-native-fog-candidate'
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def imports(path):
    data=path.read_bytes(); pe=struct.unpack_from('<I',data,0x3c)[0]
    count=struct.unpack_from('<H',data,pe+6)[0]; size=struct.unpack_from('<H',data,pe+20)[0]
    sections=[struct.unpack_from('<4I',data,pe+24+size+40*i+8) for i in range(count)]
    def offset(rva):
        for vs,va,rs,rp in sections:
            if va<=rva<va+rs:return rp+rva-va
        raise ValueError(hex(rva))
    table=offset(struct.unpack_from('<I',data,pe+24+112+8)[0]); names=[]
    while any(data[table:table+20]):
        rva=struct.unpack_from('<I',data,table+12)[0]; start=offset(rva)
        names.append(data[start:data.index(b'\0',start)].decode().lower()); table+=20
    return sorted(names)
unchanged=['CameraBoost.c','CameraStubs.S','GeometryLOD.h','HidExports.c','hid.def','export-manifest.json']
for name in unchanged:
    assert (folder/name).read_bytes()==(root/'outputs/camera-native'/name).read_bytes(),name
baseline_imports=imports(root/'outputs/camera-native/hid.dll')
candidate_imports=imports(folder/'hid.dll')
assert candidate_imports==baseline_imports,(candidate_imports,baseline_imports)
log=(root/'work/fog-candidate-build-test.log').read_text()
for text in ['PhotoFogProbe passed','baseline lifecycle/teardown/metadata guards',
             'owner filtering, normal/Shift/release speeds','"all_exports_resolved": 44']:
    assert text in log,text
manifest={'game_sha256':'51299faca61866cf10ea9035a15b8f22600a56557dd5ffc1aad390d5a54e6d82',
          'dll_sha256':digest(folder/'hid.dll'),'previous_confirmed_dll_sha256':digest(root/'outputs/camera-native/hid.dll'),
          'installed':False,'runtime_status':'Isolated tests passed; native candidate not yet runtime-confirmed.',
          'unchanged_sources':unchanged,'dependencies':candidate_imports,
          'source_hashes':{path.name:digest(path) for path in folder.iterdir() if path.suffix in ('.c','.h','.S','.def')},
          'diagnostic_user_confirmed':'Near numeric fog at far position restores dark pit fog on Corson V; both range-only tests had no visible change.',
          'isolated_tests':['real callsite relay ABI and original callback','exact-byte refusal and eight-byte CAS restoration',
                            'capture with preference off then toggle on','primary-view filtering and clone-index guard',
                            'Photo exit/reentry and snapshot renewal','texture-tail preservation',
                            'Ctrl rising edge, held/focus/startup guards','normal/Shift/release and camera ownership',
                            'no-clip and geometry disable restoration','44 HID exports and unsupported-process refusal'],
          'limitation':'Fog numeric entry snapshot; dynamic regional fog changes are deliberately held while Photo preference is enabled. Lighting is not fixed.',
          'review':'work/photo-fog-candidate-review-luna.md'}
assert manifest['previous_confirmed_dll_sha256']=='5c36943c6dfb45713382bf471e6f9939f857ee94f7789b8fefb2fc3abc292842'
assert manifest['dll_sha256']=='228620169d5741cd57d544047d351e7bd3c7df541778bc78c17ea0655bcb6f2a'
(folder/'build-verification.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'dll_sha256':manifest['dll_sha256'],'dependencies':candidate_imports,'unchanged_sources':unchanged,'isolated_tests_passed':True},indent=2))
