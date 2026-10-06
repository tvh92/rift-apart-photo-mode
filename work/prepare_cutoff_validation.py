"""Retarget the lighting-v2 regression probes and proxy test to lighting-v3.

v3 keeps every v2 source file byte-identical except PhotoLOD.h (includes and
prepares PhotoCutoff.h, logs its counter). The probes are copied unchanged
apart from the package path so v2 behaviour is re-verified against v3.
"""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
abi = root / 'work/native-abi'
probes = ['PhotoLightSpecularProbe', 'PhotoType4Probe', 'PhotoFogSpecularProbe', 'PhotoSpecularLifecycleProbe',
          'BehaviorSpecularProbe', 'SpecularStatusBitmapProbe', 'SpecularStatusThreadProbe']
for name in probes:
    text = (abi / f'{name}.c').read_text()
    assert 'camera-native-lighting-v2' in text, name
    (abi / f'{name}V3.c').write_text(text.replace('camera-native-lighting-v2', 'camera-native-lighting-v3'))
text = (root / 'work/test_specular_native_proxy.py').read_text()
(root / 'work/test_cutoff_native_proxy.py').write_text(text.replace('camera-native-lighting-v2', 'camera-native-lighting-v3'))
print('Prepared v3 regression probes:', ', '.join(p + 'V3' for p in probes))
