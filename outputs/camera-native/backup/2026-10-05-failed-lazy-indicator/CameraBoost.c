/* Native Photo Mode boost for the single verified Rift Apart executable build.
 * HID forwarding is independent of camera hooks. No heap scans or save writes.
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <bcrypt.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

#ifndef HID_EXPORT_COUNT
#error Build with the generated HID export count.
#endif
void *hid_targets[HID_EXPORT_COUNT];
extern const char *hid_names[HID_EXPORT_COUNT];
extern const unsigned short hid_ordinals[HID_EXPORT_COUNT];
extern void HookFreeStub(void);
extern void HookMotionStub(void);
void *original_free;
void *original_motion;
static HMODULE own_module,real_hid;
static INIT_ONCE proxy_once=INIT_ONCE_STATIC_INIT;
static SRWLOCK motion_lock=SRWLOCK_INIT;
static uintptr_t game_base;
static volatile LONG free_id;
static int normal_speed=10,boost_speed=100,tether=1000;
static volatile LONG enabled=TRUE;
static BOOL stop_key_down,no_clip=TRUE;
static volatile CHAR *collision_branch;
static BOOL collision_changed;
static HANDLE log_file=INVALID_HANDLE_VALUE;
static wchar_t ini_path[MAX_PATH];
static uintptr_t last_motion;
static DWORD last_motion_id;
static float original_values[4];
static int last_state=-1;

static void log_line(const char *text) {
    if(log_file!=INVALID_HANDLE_VALUE) {
        DWORD written;WriteFile(log_file,text,(DWORD)strlen(text),&written,NULL);
        WriteFile(log_file,"\r\n",2,&written,NULL);FlushFileBuffers(log_file);
    }
}
static void open_log(void) {
    wchar_t path[MAX_PATH];GetModuleFileNameW(own_module,path,MAX_PATH);
    wchar_t *slash=wcsrchr(path,L'\\');if(!slash)return;
    slash[1]=0;wcscpy(ini_path,path);wcscat(ini_path,L"PhotoModeCamera.ini");
    wcscat(path,L"PhotoModeCamera.log");
    log_file=CreateFileW(path,GENERIC_WRITE,FILE_SHARE_READ|FILE_SHARE_WRITE,NULL,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,NULL);
}
static BOOL hash_matches(const wchar_t *path) {
    static const unsigned char expected[32]={
        0x51,0x29,0x9f,0xac,0xa6,0x18,0x66,0xcf,0x10,0xea,0x90,0x35,0xa1,0x5b,0x8f,0x22,
        0x60,0x0a,0x56,0x55,0x7d,0xd5,0xff,0xc1,0xaa,0xd3,0x90,0xd5,0xa5,0x4e,0x6d,0x82};
    BOOL ok=FALSE;BCRYPT_ALG_HANDLE algorithm=NULL;BCRYPT_HASH_HANDLE hash=NULL;
    DWORD object_size=0,got=0;PUCHAR object=NULL;HANDLE file=INVALID_HANDLE_VALUE;
    unsigned char digest[32],buffer[65536];
    if(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,NULL,0)<0)goto done;
    if(BCryptGetProperty(algorithm,BCRYPT_OBJECT_LENGTH,(PUCHAR)&object_size,sizeof(object_size),&got,0)<0)goto done;
    object=HeapAlloc(GetProcessHeap(),0,object_size);if(!object)goto done;
    if(BCryptCreateHash(algorithm,&hash,object,object_size,NULL,0,0)<0)goto done;
    file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,FILE_FLAG_SEQUENTIAL_SCAN,NULL);
    if(file==INVALID_HANDLE_VALUE)goto done;
    for(;;) {
        if(!ReadFile(file,buffer,sizeof(buffer),&got,NULL))goto done;
        if(!got)break;
        if(BCryptHashData(hash,buffer,got,0)<0)goto done;
    }
    if(BCryptFinishHash(hash,digest,sizeof(digest),0)<0)goto done;
    ok=memcmp(digest,expected,sizeof(expected))==0;
done:
    if(file!=INVALID_HANDLE_VALUE)CloseHandle(file);
    if(hash)BCryptDestroyHash(hash);
    if(object)HeapFree(GetProcessHeap(),0,object);
    if(algorithm)BCryptCloseAlgorithmProvider(algorithm,0);
    return ok;
}
static BOOL replace_slot(void **slot,void *expected,void *replacement) {
    DWORD protection,unused;
    if(!VirtualProtect(slot,sizeof(void*),PAGE_READWRITE,&protection))return FALSE;
    void *prior=InterlockedCompareExchangePointer((void *volatile*)slot,replacement,expected);
    BOOL protected_again=VirtualProtect(slot,sizeof(void*),protection,&unused);
    if(!protected_again) {
        if(prior==expected)InterlockedCompareExchangePointer((void *volatile*)slot,expected,replacement);
        VirtualProtect(slot,sizeof(void*),protection,&unused);
    }
    return prior==expected && protected_again;
}
/* This single-byte branch belongs to PhotomodeCameraMotionFly::UpdateMiddle.
 * It follows the collision query and controls only its hit-position correction.
 * Query construction, destruction, tether and the final position store remain
 * native. The executable file is never changed. No gameplay collision path is
 * patched. Radius zero would still run the query and is not a no-clip switch.
 */
static BOOL set_collision_bypass(BOOL bypass) {
    if(!collision_branch)return FALSE;
    CHAR expected=bypass?0x74:(CHAR)0xeb,replacement=bypass?(CHAR)0xeb:0x74;
    if(collision_changed==bypass)return TRUE;
    DWORD protection,unused;
    if(!VirtualProtect((void*)collision_branch,1,PAGE_EXECUTE_READWRITE,&protection))return FALSE;
    CHAR prior=expected;
    BOOL exchanged=__atomic_compare_exchange_n(collision_branch,&prior,replacement,FALSE,__ATOMIC_SEQ_CST,__ATOMIC_SEQ_CST);
    BOOL restored=VirtualProtect((void*)collision_branch,1,protection,&unused);
    BOOL flushed=FlushInstructionCache(GetCurrentProcess(),(void*)collision_branch,1);
    if(exchanged && (!restored || !flushed)) {
        /* Do not leave an optional patch active after a failed page/cache check. */
        DWORD rollback_protection;
        if(VirtualProtect((void*)collision_branch,1,PAGE_EXECUTE_READWRITE,&rollback_protection)) {
            CHAR rollback_expected=replacement;
            BOOL rolled_back=__atomic_compare_exchange_n(collision_branch,&rollback_expected,expected,FALSE,__ATOMIC_SEQ_CST,__ATOMIC_SEQ_CST);
            VirtualProtect((void*)collision_branch,1,protection,&unused);
            FlushInstructionCache(GetCurrentProcess(),(void*)collision_branch,1);
            if(rolled_back)exchanged=FALSE;
        }
    }
    if(exchanged)collision_changed=bypass;
    return exchanged && restored && flushed;
}
static BOOL prepare_collision_bypass(unsigned char *call_site) {
    static const unsigned char expected[9]={0xe8,0x44,0xaa,0x75,0xff,0x84,0xc0,0x74,0x3b};
    if(memcmp(call_site,expected,sizeof(expected)))return FALSE;
    collision_branch=(volatile CHAR*)(call_site+7);
    return set_collision_bypass(TRUE);
}
#include "PhotoLOD.h"
static DWORD WINAPI start_camera(LPVOID unused) {
    (void)unused;open_log();log_line("HID proxy loaded; verifying camera build.");
    wchar_t executable[MAX_PATH];GetModuleFileNameW(NULL,executable,MAX_PATH);
    wchar_t *name=wcsrchr(executable,L'\\');
    if(!name || _wcsicmp(name+1,L"RiftApart.exe") || !hash_matches(executable)) {
        log_line("Unsupported executable: HID forwarding only; camera hooks disabled.");return 0;
    }
    normal_speed=(int)GetPrivateProfileIntW(L"Camera",L"Normal",10,ini_path);
    boost_speed=(int)GetPrivateProfileIntW(L"Camera",L"Boost",100,ini_path);
    tether=(int)GetPrivateProfileIntW(L"Camera",L"Tether",1000,ini_path);
    int collision_setting=(int)GetPrivateProfileIntW(L"Camera",L"NoClip",1,ini_path);
    int lod_setting=(int)GetPrivateProfileIntW(L"Camera",L"GeometryLOD",1,ini_path);
    no_clip=collision_setting==1;
    geometry_enabled=lod_setting==1;
    if(normal_speed<1 || normal_speed>1000 || boost_speed<1 || boost_speed>1000 || tether<1 || tether>10000 || collision_setting<0 || collision_setting>1 || lod_setting<0 || lod_setting>1) {
        log_line("Invalid INI values: camera hooks disabled.");return 0;
    }
    /* Hook targets must never outlive this DLL, even if another tool attempts
       FreeLibrary. Pin it for the lifetime of the process before patching. */
    HMODULE pinned;
    if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_PIN,(LPCWSTR)(uintptr_t)start_camera,&pinned)) {
        log_line("Unable to pin hook module: camera hooks disabled.");return 0;
    }
    game_base=(uintptr_t)GetModuleHandleW(NULL);
    void **free_slot=(void**)(game_base+0x45fd8b0+12*8);
    void **motion_slot=(void**)(game_base+0x45fdef0+10*8);
    original_free=(void*)(game_base+0x1a5d4d0);
    original_motion=(void*)(game_base+0x1a5eba0);
    if(*free_slot!=original_free || *motion_slot!=original_motion) {
        log_line("Hook slots already changed: camera hooks disabled.");return 0;
    }
    if(!replace_slot(free_slot,original_free,(void*)HookFreeStub)) {
        log_line("Unable to install Free-camera hook.");return 0;
    }
    if(!replace_slot(motion_slot,original_motion,(void*)HookMotionStub)) {
        replace_slot(free_slot,(void*)HookFreeStub,original_free);
        log_line("Unable to install movement hook; Free hook rolled back.");return 0;
    }
    if(no_clip) {
        if(prepare_collision_bypass((unsigned char*)(game_base+0x1a5f1e7)))
            log_line("Photo Mode collision-response bypass installed.");
        else log_line("Collision guard/protection check failed; no-clip unavailable. Speed hooks remain enabled.");
    }
    if(geometry_enabled && !prepare_photo_geometry())log_line("Geometry LOD guards/install failed; native LOD retained. Camera controls remain enabled.");
    char message[160];snprintf(message,sizeof(message),"Camera hooks installed. Normal=%d Boost=%d Tether=%d",normal_speed,boost_speed,tether);
    log_line(message);return 0;
}
static BOOL CALLBACK initialize_proxy(PINIT_ONCE once,PVOID parameter,PVOID *context) {
    (void)once;(void)parameter;(void)context;
    wchar_t system_path[MAX_PATH];UINT n=GetSystemDirectoryW(system_path,MAX_PATH);
    if(!n || n>=MAX_PATH-9)return FALSE;
    wcscat(system_path,L"\\hid.dll");
    real_hid=LoadLibraryExW(system_path,NULL,LOAD_LIBRARY_SEARCH_SYSTEM32);
    if(!real_hid)return FALSE;
    for(unsigned i=0;i<HID_EXPORT_COUNT;i++) {
        hid_targets[i]=(void*)GetProcAddress(real_hid,hid_names[i]?hid_names[i]:(LPCSTR)(uintptr_t)hid_ordinals[i]);
        if(!hid_targets[i])return FALSE;
    }
    HANDLE worker=CreateThread(NULL,0,start_camera,NULL,0,NULL);
    if(worker)CloseHandle(worker);
    return TRUE;
}
void EnsureProxy(void) {
    if(!InitOnceExecuteOnce(&proxy_once,initialize_proxy,NULL,NULL)) {
        /* No valid forwarding target exists: fail explicitly instead of jumping
           through a null pointer or running against an incompatible system DLL. */
        RaiseFailFastException(NULL,NULL,0);
    }
}
void CaptureFree(void *camera) {
    uintptr_t p=(uintptr_t)camera;
    if(*(uintptr_t*)p!=game_base+0x45fd8b0 ||
       *(uintptr_t*)(p+0xd8)!=game_base+0x4690b30 ||
       *(uintptr_t*)(p+0xf0)!=game_base+0x4690a50)return;
    LONG id=*(LONG*)(p+0x1c);
    LONG prior=InterlockedExchange(&free_id,id);
    if(id!=prior) {
        char message[96];snprintf(message,sizeof(message),"Free camera activated: id=%08lx",(unsigned long)id);log_line(message);
    }
}
void UpdateMotion(void *motion) {
    uintptr_t p=(uintptr_t)motion;
    if(*(uintptr_t*)p!=game_base+0x45fdef0 || !free_id || *(LONG*)(p+0x44)!=free_id)return;
    AcquireSRWLockExclusive(&motion_lock);
    if(*(LONG*)(p+0x44)!=free_id) { ReleaseSRWLockExclusive(&motion_lock);return; }
    DWORD id=*(DWORD*)(p+0x1c);
    float *distance=(float*)(p+0x68),*move=(float*)(p+0x6c),*acceleration=(float*)(p+0x70),*rise=(float*)(p+0x84);
    if(last_motion!=p || last_motion_id!=id) {
        float values[4]={*distance,*move,*rise,*acceleration};
        if(!isfinite(values[0]) || !isfinite(values[1]) || !isfinite(values[2]) || !isfinite(values[3]) ||
           values[0]<=0 || values[0]>10000 || values[1]<0 || values[1]>2000 ||
           values[2]<0 || values[2]>1000 || values[3]<0 || values[3]>1000000) {
            ReleaseSRWLockExclusive(&motion_lock);return;
        }
        memcpy(original_values,values,sizeof(values));last_motion=p;last_motion_id=id;last_state=-1;
        log_line("Matched live Free-camera movement controller.");
    }
    BOOL stop=(GetAsyncKeyState(VK_CONTROL)&0x8000) && (GetAsyncKeyState(VK_MENU)&0x8000) && (GetAsyncKeyState(VK_F10)&0x8000);
    if(stop && !stop_key_down) {
        InterlockedExchange(&enabled,FALSE);
        InterlockedExchange(&geometry_active,0);
        ShowPhotoIndicator(FALSE,GetForegroundWindow());
        if(geometry_ready) {
            if(geometry_restore(&geometry_patch))log_line("Native geometry LOD selector bytes restored.");
            else log_line("Geometry restore conflict; preference gate remains disabled.");
        }
        if(collision_changed) {
            if(set_collision_bypass(FALSE))log_line("Original Photo Mode collision response restored.");
            else log_line("Unable to restore collision response; restart with NoClip=0 to restore it.");
        }
    }
    stop_key_down=stop;
    DWORD foreground_pid=0;GetWindowThreadProcessId(GetForegroundWindow(),&foreground_pid);
    BOOL boost=enabled && foreground_pid==GetCurrentProcessId() && (GetAsyncKeyState(VK_SHIFT)&0x8000);
    int state=enabled?(boost?1:0):2;
    if(enabled) {
        float speed=(float)(boost?boost_speed:normal_speed);
        *distance=(float)tether;*move=2.0f*speed;*rise=speed;*acceleration=1000.0f*speed;
    } else {
        *distance=original_values[0];*move=original_values[1];*rise=original_values[2];*acceleration=original_values[3];
    }
    if(state!=last_state) {
        log_line(state==1?"Shift boost active.":state==0?"Normal camera speed active.":"Runtime boost disabled; controller baseline restored.");
        last_state=state;
    }
    ReleaseSRWLockExclusive(&motion_lock);
}
BOOL WINAPI DllMain(HINSTANCE module,DWORD reason,LPVOID reserved) {
    (void)reserved;
    if(reason==DLL_PROCESS_ATTACH) { own_module=module;DisableThreadLibraryCalls(module); }
    return TRUE;
}
