/* Build-specific Photo lifecycle adapter for the geometry-only LOD candidate. */
#include "GeometryLOD.h"
#include "PhotoIndicator.h"
extern void HookPhotoDestroyStub(void),HookPhotoCleanupStub(void);
void *original_photo_destroy,*original_photo_cleanup;
static void *original_photo_metadata,*original_photo_tick;
static SRWLOCK photo_install_lock=SRWLOCK_INIT;
static GeometryPatch geometry_patch;
static volatile LONG geometry_active;
static BOOL geometry_enabled=TRUE,photo_tick_installed;
static volatile LONG geometry_ready;
static int last_photo_state=-1;
static BOOL lod_toggle_down;
static BOOL lod_ctrl_candidate;

static void toggle_photo_geometry(void *self) {
    BOOL key=(GetAsyncKeyState(VK_CONTROL)&0x8000)!=0;
    BOOL chord=(GetAsyncKeyState(VK_MENU)&0x8000) || (GetAsyncKeyState(VK_SHIFT)&0x8000) ||
        (GetAsyncKeyState(VK_LWIN)&0x8000) || (GetAsyncKeyState(VK_RWIN)&0x8000) || (GetAsyncKeyState(VK_F10)&0x8000);
    uintptr_t p=(uintptr_t)self;DWORD foreground=0;
    GetWindowThreadProcessId(GetForegroundWindow(),&foreground);
    BOOL allowed=enabled && geometry_ready && p &&
       *(uintptr_t*)p==game_base+0x2fbf630 && *(int*)(p+0x50)==4 &&
       *(unsigned char*)(p+0x54)==1 && foreground==GetCurrentProcessId();
    /* Toggle on release: a Ctrl press that becomes Alt/F10 or Shift chord
     * must never toggle detail. A held Ctrl across focus/entry is rejected. */
    if(key && !lod_toggle_down)lod_ctrl_candidate=allowed && !chord;
    if(!allowed || chord)lod_ctrl_candidate=FALSE;
    if(!key && lod_toggle_down && lod_ctrl_candidate && allowed) {
        geometry_enabled=!geometry_enabled;
        log_line(geometry_enabled?"Geometry LOD comparison: highest preference enabled.":"Geometry LOD comparison: native preference enabled.");
    }
    if(!key)lod_ctrl_candidate=FALSE;
    lod_toggle_down=key;
}

static void update_photo_gate(void *self) {
    uintptr_t p=(uintptr_t)self;
    if(!p || *(uintptr_t*)p!=game_base+0x2fbf630) {
        InterlockedExchange(&geometry_active,0);return;
    }
    int state=*(int*)(p+0x50);
    /* Proven ordinary entry/loading/Free-camera states. Other states fail
     * closed pending their own evidence; state6/12 close before restoration. */
    BOOL active=geometry_ready && geometry_enabled && enabled &&
        *(unsigned char*)(p+0x54)==1 && (state==1 || state==2 || state==4);
    LONG prior=InterlockedExchange(&geometry_active,active?1:0);
    if(state==4 && (state!=last_photo_state || prior!=(active?1:0)))ShowPhotoIndicator(active,GetForegroundWindow());
    if(state==6 || state==12 || state==14)HidePhotoIndicator();
    if(state!=last_photo_state || prior!=(active?1:0)) {
        char message[120];snprintf(message,sizeof(message),"Photo lifecycle state=%d; geometry LOD preference=%s.",state,active?"highest":"native");
        log_line(message);last_photo_state=state;
    }
}

void ClearPhotoLOD(void *self) {
    (void)self;
    if(InterlockedExchange(&geometry_active,0))log_line("Photo teardown: native geometry LOD preference restored.");
    last_photo_state=-1;
    lod_ctrl_candidate=FALSE;HidePhotoIndicator();
}

static void HookPhotoTick(void *self) {
    /* This verified callback is void(PhotoSystem*), with no stack arguments.
     * Check both sides: disable before Stop/teardown; enable after Enter has
     * saved native state and completed its dispatch. Never retain self. */
    toggle_photo_geometry(self);
    update_photo_gate(self);
    ((void (*)(void*))original_photo_tick)(self);
    update_photo_gate(self);
}

static BOOL install_photo_tick(void *table) {
    if((uintptr_t)table!=game_base+0x61381b0)return FALSE;
    AcquireSRWLockExclusive(&photo_install_lock);
    BOOL result=photo_tick_installed;
    void **slot=(void**)((uintptr_t)table+0x18);
    if(!result && *(void**)table==(void*)(game_base+0x8dfd50) && *slot==original_photo_tick) {
        result=replace_slot(slot,original_photo_tick,(void*)HookPhotoTick);
        if(result) {photo_tick_installed=TRUE;log_line("Photo lifecycle callback hooked; geometry LOD candidate is ready.");}
    }
    ReleaseSRWLockExclusive(&photo_install_lock);
    return result;
}

static void *HookPhotoMetadata(void *self) {
    /* Original getter ignores self and returns a lazily initialized table.
     * Run it first so the game's initializer cannot overwrite our callback. */
    void *table=((void*(*)(void*))original_photo_metadata)(self);
    install_photo_tick(table);
    return table;
}

static BOOL prepare_photo_geometry(void) {
    DWORD64 image_base[2]={0};
    RUNTIME_FUNCTION functions[2];
    const DWORD starts[2]={0x111a700,0x111a910},ends[2]={0x111a90b,0x111aa71};
    for(int i=0;i<2;i++) {
        RUNTIME_FUNCTION *f=RtlLookupFunctionEntry(game_base+starts[i],&image_base[i],NULL);
        if(!f || image_base[i]!=game_base || f->BeginAddress!=starts[i] || f->EndAddress!=ends[i])return FALSE;
        functions[i]=*f;
    }
    IMAGE_DOS_HEADER *dos=(IMAGE_DOS_HEADER*)game_base;
    IMAGE_NT_HEADERS64 *nt=(IMAGE_NT_HEADERS64*)(game_base+dos->e_lfanew);
    if(nt->OptionalHeader.SizeOfImage!=0x7155000)return FALSE;
    if(!geometry_prepare(&geometry_patch,game_base,game_base+0x7155000,
        (unsigned char*)(game_base+0x111a860),(unsigned char*)(game_base+0x111a9e8),&geometry_active,functions))return FALSE;
    void **vt=(void**)(game_base+0x2fbf630);
    original_photo_destroy=(void*)(game_base+0x8dc3e0);
    original_photo_cleanup=(void*)(game_base+0x8dd0c0);
    original_photo_metadata=(void*)(game_base+0x8dda80);
    original_photo_tick=(void*)(game_base+0x8dfa70);
    if(vt[0]!=original_photo_destroy || vt[2]!=original_photo_cleanup || vt[12]!=original_photo_metadata)return FALSE;
    if(!replace_slot(vt,original_photo_destroy,(void*)HookPhotoDestroyStub))return FALSE;
    if(!replace_slot(vt+2,original_photo_cleanup,(void*)HookPhotoCleanupStub)) {
        replace_slot(vt,(void*)HookPhotoDestroyStub,original_photo_destroy);return FALSE;
    }
    /* Publish the lazy callback hook only after selector installation succeeds.
     * A failed selector install must not race with metadata initialization. */
    if(!geometry_install(&geometry_patch))goto rollback;
    if(!replace_slot(vt+12,original_photo_metadata,(void*)HookPhotoMetadata)) {
        geometry_restore(&geometry_patch);goto rollback;
    }
    InterlockedExchange(&geometry_ready,TRUE);
    StartPhotoIndicator();
    /* The table may already have been initialized before the worker started. */
    install_photo_tick((void*)(game_base+0x61381b0));
    log_line("Guarded geometry-only LOD candidate installed; awaiting Photo Mode activation.");
    return TRUE;
rollback:
    replace_slot(vt+2,(void*)HookPhotoCleanupStub,original_photo_cleanup);
    replace_slot(vt,(void*)HookPhotoDestroyStub,original_photo_destroy);
    return FALSE;
}
