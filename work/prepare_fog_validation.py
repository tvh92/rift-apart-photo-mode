"""Prepare isolated existing camera/lifecycle tests against the separate candidate."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
folder=root/'work/native-abi'
for name in ('PhotoLifecycleProbe','BehaviorProbe'):
    source=(folder/(name+'.c')).read_text(encoding='utf-8')
    source=source.replace('../../outputs/camera-native/CameraBoost.c','../../outputs/camera-native-fog-candidate/CameraBoost.c')
    if name=='PhotoLifecycleProbe':
        source=source.replace('if(geometry_active!=((s==1 || s==2 || s==4)?1:0))return 1;',
                              'if(geometry_active!=((s==1 || s==2 || s==4)?1:0))return 1;\n        if(photo_fog_session!=((s==1 || s==2 || s==4)?1:0))return 51;')
        source=source.replace('if(geometry_active)return 3;',
                              'if(geometry_active || photo_fog_session || photo_fog_cached)return 3;')
    (folder/(name.replace('Probe','FogIntegrationProbe')+'.c')).write_text(source,encoding='utf-8')
source=(root/'work/test_native_proxy.py').read_text(encoding='utf-8')
source=source.replace("root=Path('outputs/camera-native').resolve()","root=Path('outputs/camera-native-fog-candidate').resolve()")
(root/'work/test_fog_native_proxy.py').write_text(source,encoding='utf-8')
