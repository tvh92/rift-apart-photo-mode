"""Reuse meaningful camera/fog regression probes against the lighting candidate."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for name in ('PhotoLifecycleFogIntegrationProbe','BehaviorFogIntegrationProbe','PhotoFogProbe'):
    src=(root/'work/native-abi'/f'{name}.c').read_text()
    src=src.replace('camera-native-fog-candidate','camera-native-lighting-candidate')
    dest=name.replace('FogIntegration','LightIntegration') if 'Integration' in name else 'PhotoFogLightIntegrationProbe'
    (root/'work/native-abi'/f'{dest}.c').write_text(src)
src=(root/'work/test_fog_native_proxy.py').read_text().replace('camera-native-fog-candidate','camera-native-lighting-candidate')
(root/'work/test_light_native_proxy.py').write_text(src)
