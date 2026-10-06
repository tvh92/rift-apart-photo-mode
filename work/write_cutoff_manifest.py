"""Write lighting-v3 build-verification.json after a passing build/test run."""
import hashlib
import json
import struct
from pathlib import Path

root = Path(__file__).resolve().parents[1]
v2, v3 = root / 'outputs/camera-native-lighting-v2', root / 'outputs/camera-native-lighting-v3'
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def imports(path):
    data = path.read_bytes()
    pe = struct.unpack_from('<I', data, 0x3C)[0]
    sections = struct.unpack_from('<H', data, pe + 6)[0]
    optional = struct.unpack_from('<H', data, pe + 20)[0]
    rva = struct.unpack_from('<I', data, pe + 24 + 112 + 8)[0]
    table = [struct.unpack_from('<IIIII', data, pe + 24 + optional + i * 40 + 8) for i in range(sections)]
    def offset(value):
        for size, address, _, raw, _ in table:
            if address <= value < address + max(size, 1):
                return value - address + raw
        raise ValueError(hex(value))
    names, at = [], offset(rva)
    while True:
        entry = struct.unpack_from('<5I', data, at)
        if not any(entry):
            break
        start = offset(entry[3])
        names.append(data[start:data.index(b'\0', start)].decode().lower())
        at += 20
    return sorted(names)


log = (root / 'work/cutoff-candidate-build-test.log').read_text(encoding='utf-8', errors='replace')
required = ['PhotoCutoffProbe passed', 'PhotoLightProbe passed', 'PhotoType4Probe passed', 'PhotoFogProbe passed',
            '"all_exports_resolved": 44', 'refused correctly']
missing = [r for r in required if r not in log]
if missing:
    raise SystemExit(f'Build/test log incomplete: {missing}')
v2_manifest = json.loads((v2 / 'build-verification.json').read_text(encoding='utf-8-sig'))
deps = imports(v3 / 'hid.dll')
if deps != sorted(v2_manifest['dependencies']):
    raise SystemExit(f'Dependency set changed: {deps}')
sources = ['CameraBoost.c', 'CameraStubs.S', 'GeometryLOD.h', 'hid.def', 'HidExports.c', 'PhotoFog.h',
           'PhotoIndicator.h', 'PhotoLight.h', 'PhotoLOD.h', 'PhotoSpecular.h', 'PhotoCutoff.h']
unchanged = [s for s in sources if (v2 / s).exists() and sha(v2 / s) == sha(v3 / s)]
manifest = {
    'game_sha256': sha(GAME / 'RiftApart.exe'),
    'dll_sha256': sha(v3 / 'hid.dll'),
    'previous_dll_sha256': v2_manifest['dll_sha256'],
    'installed': False,
    'install_blocked_reason': None,
    'runtime_status': 'Built and isolated-tested; not installed.',
    'unchanged_sources': unchanged + ['export-manifest.json'],
    'changed_sources': [s for s in sources if s not in unchanged],
    'dependencies': deps,
    'source_hashes': {s: sha(v3 / s).upper() for s in sources},
    'new_behaviour': ('Light filter job 10B9A50: for the primary Photo view with Ctrl on, the bit18 '
                      'pre-upload far drop (front distance > rec+A0) is skipped; all other filters, '
                      'source records and non-primary views unchanged.'),
    'native_sites': ['1099270 and 10BE260 unchanged from v2',
                     '10B9C00: aligned8 JMP to registered CHAININFO leaf relay; replays comiss/ja otherwise'],
    'isolated_tests': [line.strip() for line in log.splitlines() if 'passed' in line or line.startswith('PASS') or 'example' in line],
    'review': 'work/photo-cutoff-actual-source-review.txt',
    'limitations': ('Lights beyond the cutoff now enter ranking; the 512-entry merge cap and ranking buckets, '
                    'occlusion, near fade, type/colour, eligibility masks and shader capacity remain native. '
                    'Runtime visual result and performance unconfirmed.'),
}
(v3 / 'build-verification.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: manifest[k] for k in ('dll_sha256', 'previous_dll_sha256', 'changed_sources', 'dependencies')}, indent=1))
