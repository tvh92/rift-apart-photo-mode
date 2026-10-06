"""Verify the built controls update, then audit an already-installed candidate."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / 'outputs/camera-native'
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

manifest = json.loads((NATIVE / 'build-verification.json').read_text(encoding='utf-8-sig'))
assert digest(NATIVE / 'hid.dll') == manifest['dll_sha256']
for name, expected in manifest['source_sha256'].items():
    assert digest(NATIVE / name) == expected, f'Source changed after verification: {name}'
assert digest(NATIVE / 'backup/2026-10-05-before-control-indicator/hid.dll') == manifest['previous_geometry_dll_sha256']
assert digest(GAME / 'PhotoModeCamera.ini') == '2742e230e680046e4833173c6a435822aaa319999d9626608381118ad7ff34e9'
print('PASS: candidate/source hashes, previous geometry rollback, unchanged installed INI.')

if '--installed' in sys.argv:
    assert digest(GAME / 'hid.dll') == manifest['dll_sha256']
    spec = importlib.util.spec_from_file_location('camera_audit', ROOT / 'outputs/camera-controls/Check-Installation.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.audit()
    report['unchanged_ini_verified'] = True
    report['previous_geometry_rollback_verified'] = True
    report['control_indicator_in_game'] = 'Awaiting user test; isolated probes pass.'
    report['lighting_and_pit_fog'] = 'User reports missing surface illumination and white fog in Corson V; not patched.'
    (NATIVE / 'controls-indicator-installation-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
