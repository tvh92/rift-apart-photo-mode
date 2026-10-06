"""Reuse status regressions and adapt the real relay test to diffuse+specular."""
from pathlib import Path
root=Path(__file__).resolve().parents[1];abi=root/'work/native-abi'
pairs=[('PhotoLightStatusProbe','PhotoLightSpecularProbe'),('PhotoFogStatusProbe','PhotoFogSpecularProbe'),
       ('PhotoStatusLifecycleProbe','PhotoSpecularLifecycleProbe'),('BehaviorStatusProbe','BehaviorSpecularProbe'),
       ('StatusBitmapProbe','SpecularStatusBitmapProbe'),('StatusThreadProbe','SpecularStatusThreadProbe')]
for old,new in pairs:
    s=(abi/f'{old}.c').read_text().replace('camera-native-status-candidate','camera-native-lighting-v2')
    if old=='PhotoLightStatusProbe':
        s=s.replace('evaluate(invoke,light,flags,fronts[f],centres[c],view,expected)',
                    'evaluate(invoke,light,flags&~(1u<<20),fronts[f],centres[c],view,expected)')
        s=s.replace('    if(photo_light_hits!=1920)return 16;', '''    if(photo_light_hits!=1920)return 16;
    set_float(light,0xa4,70);*(unsigned char*)(game_base+0x53394ec)=0;
    *(unsigned*)(light+0x88)=1u<<20;unsigned old_kind=99;
    foreign(light,85,80,expected,expected+3,&old_kind);
    if(!evaluate(invoke,light,(1u<<18)|(1u<<20),85,80,view,actual))return 70;
    if(!same(expected[3],0) || old_kind!=1 || !same(actual[3],.7f) || actual[4]!=0)return 71;
    printf("Ordinary specular example at85: prior RGB-only override specular=%g/type=%u; new specular=%g/type=%g.\\n",expected[3],old_kind,actual[3],actual[4]);''')
    (abi/f'{new}.c').write_text(s)
s=(root/'work/test_status_native_proxy.py').read_text().replace('camera-native-status-candidate','camera-native-lighting-v2')
(root/'work/test_specular_native_proxy.py').write_text(s)
print('Prepared diffuse/specular relay and unchanged fog/camera/status regression probes.')
