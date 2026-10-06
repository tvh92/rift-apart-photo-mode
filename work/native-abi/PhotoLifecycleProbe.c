#include <windows.h>
static BOOL comparison_key,alt_key,shift_key;
static DWORD foreground_pid;
static SHORT FakePhotoKey(int key) {return ((comparison_key && key==VK_CONTROL) || (alt_key && key==VK_MENU) || (shift_key && key==VK_SHIFT))?(SHORT)0x8000:0;}
static HWND FakePhotoWindow(void) {return (HWND)1;}
static DWORD FakePhotoWindowPid(HWND window,LPDWORD pid) {(void)window;*pid=foreground_pid;return 1;}
#define GetAsyncKeyState FakePhotoKey
#define GetForegroundWindow FakePhotoWindow
#define GetWindowThreadProcessId FakePhotoWindowPid
#define HID_EXPORT_COUNT 44
#include "../../outputs/camera-native/CameraBoost.c"
static int next_state,expected_before,callback_failure;
static void FakeTick(void *self) {
    if(geometry_active!=expected_before)callback_failure=1;
    *(int*)((unsigned char*)self+0x50)=next_state;
}
static void *metadata_table;
static void *FakeMetadata(void *self) {(void)self;return metadata_table;}
int main(void) {
    unsigned char photo[0xc78]={0};game_base=0x10000000;
    *(uintptr_t*)photo=game_base+0x2fbf630;photo[0x54]=1;
    geometry_ready=TRUE;geometry_enabled=TRUE;
    foreground_pid=GetCurrentProcessId();
    for(int s=0;s<=15;s++) {
        *(int*)(photo+0x50)=s;update_photo_gate(photo);
        if(geometry_active!=((s==1 || s==2 || s==4)?1:0))return 1;
    }
    original_photo_tick=(void*)FakeTick;
    int states[][3]={{0,1,0},{1,2,1},{2,4,1},{4,6,1},{6,14,0},{12,14,0}};
    for(unsigned i=0;i<sizeof(states)/sizeof(states[0]);i++) {
        *(int*)(photo+0x50)=states[i][0];next_state=states[i][1];expected_before=states[i][2];
        HookPhotoTick(photo);
        if(callback_failure || geometry_active!=((next_state==1 || next_state==2 || next_state==4)?1:0))return 2;
    }
    *(int*)(photo+0x50)=4;update_photo_gate(photo);ClearPhotoLOD(photo);
    if(geometry_active)return 3;
    photo[0x54]=0;update_photo_gate(photo);if(geometry_active)return 4;
    photo[0x54]=1;enabled=FALSE;update_photo_gate(photo);if(geometry_active)return 5;
    enabled=TRUE;*(uintptr_t*)photo=0;update_photo_gate(photo);if(geometry_active)return 6;
    *(uintptr_t*)photo=game_base+0x2fbf630;foreground_pid=GetCurrentProcessId();
    *(int*)(photo+0x50)=4;next_state=4;comparison_key=TRUE;expected_before=0;HookPhotoTick(photo);
    if(geometry_enabled || geometry_active || callback_failure)return 11;
    HookPhotoTick(photo);if(geometry_enabled)return 12; /* held Ctrl does not repeat */
    comparison_key=FALSE;HookPhotoTick(photo);if(geometry_enabled)return 13;
    comparison_key=TRUE;expected_before=1;HookPhotoTick(photo);
    comparison_key=FALSE;HookPhotoTick(photo);
    if(!geometry_enabled || geometry_active!=1 || callback_failure)return 14;
    /* Pressing while unfocused cannot toggle on focus regain while held. */
    foreground_pid=0;comparison_key=TRUE;HookPhotoTick(photo);
    if(!geometry_enabled)return 17;
    foreground_pid=GetCurrentProcessId();HookPhotoTick(photo);
    if(!geometry_enabled)return 18;
    comparison_key=FALSE;HookPhotoTick(photo);
    *(int*)(photo+0x50)=6;expected_before=0;next_state=14;HookPhotoTick(photo);
    if(geometry_active)return 19;
    /* Lazy getter initializes first, then the guarded callback is replaced. */
    void **table=VirtualAlloc(NULL,4096,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
    if(!table)return 7;
    game_base=(uintptr_t)table-0x61381b0;metadata_table=table;
    table[0]=(void*)(game_base+0x8dfd50);table[3]=(void*)FakeTick;
    original_photo_metadata=(void*)FakeMetadata;
    if(HookPhotoMetadata(photo)!=table || !photo_tick_installed || table[3]!=(void*)HookPhotoTick)return 8;
    if(HookPhotoMetadata(photo)!=table || table[3]!=(void*)HookPhotoTick)return 9;
    photo_tick_installed=FALSE;table[3]=(void*)0x1234;
    if(install_photo_tick(table) || table[3]!=(void*)0x1234)return 10;
    puts("PASS: baseline lifecycle/teardown/metadata guards with Ctrl rising edge, no held repeats, and focus gate; no indicator code.");
    return 0;
}
