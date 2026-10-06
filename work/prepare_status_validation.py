"""Isolated status UI plus unchanged camera, fog and lighting regression probes."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
abi=root/'work/native-abi'
for old,new in [('PhotoLightProbe','PhotoLightStatusProbe'),
                ('PhotoFogLightIntegrationProbe','PhotoFogStatusProbe'),
                ('BehaviorLightIntegrationProbe','BehaviorStatusProbe')]:
    source=(abi/f'{old}.c').read_text().replace('camera-native-lighting-candidate','camera-native-status-candidate')
    (abi/f'{new}.c').write_text(source)
for old,new in [('IndicatorProbe','StatusBitmapProbe'),('IndicatorThreadProbe','StatusThreadProbe')]:
    source=(abi/f'{old}.c').read_text().replace('camera-native/PhotoIndicator.h','camera-native-status-candidate/PhotoIndicator.h')
    source=source.replace('indicator-on','status-on').replace('indicator-off','status-off')
    # Keep generated preview filenames separate from historical evidence.
    source=source.replace('indicator-%s.bgra','status-%s.bgra')
    (abi/f'{new}.c').write_text(source)
src=(root/'work/test_light_native_proxy.py').read_text().replace('camera-native-lighting-candidate','camera-native-status-candidate')
(root/'work/test_status_native_proxy.py').write_text(src)
source=(abi/'PhotoLifecycleLightIntegrationProbe.c').read_text().replace('camera-native-lighting-candidate','camera-native-status-candidate')
helpers='''static int indicator_start_calls;
static BOOL FakePhotoIsWindow(HWND window) {return window==(HWND)1;}
static BOOL FakePhotoIsIconic(HWND window) {(void)window;return FALSE;}
static HANDLE WINAPI FakePhotoCreateThread(LPSECURITY_ATTRIBUTES a,SIZE_T stack,LPTHREAD_START_ROUTINE fn,LPVOID arg,DWORD flags,LPDWORD id) {
    (void)a;(void)stack;(void)fn;(void)arg;(void)flags;(void)id;indicator_start_calls++;return (HANDLE)0x1234;
}
static BOOL WINAPI FakePhotoCloseHandle(HANDLE h) {return h==(HANDLE)0x1234?TRUE:CloseHandle(h);}
#define IsWindow FakePhotoIsWindow
#define IsWindowVisible FakePhotoIsWindow
#define IsIconic FakePhotoIsIconic
#define CreateThread FakePhotoCreateThread
#define CloseHandle FakePhotoCloseHandle
'''
source=source.replace('#define HID_EXPORT_COUNT 44',helpers+'#define HID_EXPORT_COUNT 44')
source=source.replace('    for(int s=0;s<=15;s++) {','''    int startup_states[]={14,10,11,0,1,2};
    for(unsigned i=0;i<sizeof(startup_states)/sizeof(startup_states[0]);i++) {
        *(int*)(photo+0x50)=startup_states[i];update_photo_gate(photo);
        if(indicator_start_calls || indicator_started || indicator_thread_id)return 60;
    }
    for(int s=0;s<=15;s++) {''')
source=source.replace('    HookPhotoTick(photo);if(geometry_enabled)return 12;',
                      '    if(indicator_pending_mode!=0)return 61;\n    HookPhotoTick(photo);if(geometry_enabled || indicator_pending_mode!=0)return 12;')
source=source.replace('    if(!geometry_enabled || geometry_active!=1 || callback_failure)return 14;',
                      '    if(!geometry_enabled || geometry_active!=1 || callback_failure || indicator_pending_mode!=1)return 14;')
source=source.replace('    if(geometry_active)return 19;',
                      '    if(geometry_active || indicator_pending_mode!=-1)return 19;')
source=source.replace('    puts("PASS: baseline lifecycle/teardown/metadata guards with Ctrl rising edge, no held repeats, and focus gate; no indicator code.");',
'''    if(indicator_start_calls!=1)return 62;
    puts("PASS: dormant startup UI, one active-Photo worker, ON/OFF/Ctrl rising-edge/focus/held guards, hide on exit, fog lifecycle and metadata guards.");''')
(abi/'PhotoStatusLifecycleProbe.c').write_text(source)
print('Prepared status UI and preserved native camera/fog/light regression probes.')
