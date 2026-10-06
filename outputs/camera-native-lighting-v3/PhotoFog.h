/* Exact-build Photo fog candidate. Overrides only a per-frame renderer block;
 * source atmosphere, texture handles, camera position and gameplay stay native.
 * Capture the numeric fog recipe on the first main-view Photo frame. */
#ifndef PHOTO_FOG_H
#define PHOTO_FOG_H
static SRWLOCK photo_fog_lock=SRWLOCK_INIT;
static BOOL photo_fog_session,photo_fog_cached;
static volatile LONG photo_fog_ready;
static unsigned char photo_fog_snapshot[0x84];
static GeometryPatch photo_fog_patch;
static void (*original_photo_fog)(void*,void*);

static void photo_fog_session_update(BOOL active) {
    AcquireSRWLockExclusive(&photo_fog_lock);
    if(photo_fog_session!=active)photo_fog_cached=FALSE;
    photo_fog_session=active;
    ReleaseSRWLockExclusive(&photo_fog_lock);
}

static void photo_fog_consider(unsigned char *block,BOOL primary) {
    if(!primary || !block)return;
    AcquireSRWLockExclusive(&photo_fog_lock);
    if(photo_fog_session) {
        if(!photo_fog_cached) {
            memcpy(photo_fog_snapshot,block+0x110,sizeof(photo_fog_snapshot));
            photo_fog_cached=TRUE;
        }
        if(InterlockedCompareExchange(&geometry_active,0,0))
            memcpy(block+0x110,photo_fog_snapshot,sizeof(photo_fog_snapshot));
    }
    ReleaseSRWLockExclusive(&photo_fog_lock);
}

static void HookPhotoPrepareFog(void *job,void *lighting,void *source_view) {
    if(!InterlockedCompareExchange(&photo_fog_ready,0,0)) {
        original_photo_fog(job,lighting);return;
    }
    unsigned char *j=job;
    /* The exact callsite relay supplies the caller's original view in R8.
     * job+570 is its native clone, so comparing that pointer directly to the
     * primary view would wrongly exclude Photo Mode. */
    BOOL primary=source_view && (uintptr_t)source_view==*(uintptr_t*)(game_base+0x6739b10);
    unsigned char *clone=*(unsigned char**)(j+0x570);
    if(primary && clone && *(int*)(clone+0xf90)==*(int*)((unsigned char*)source_view+0xf90))
        photo_fog_consider(*(unsigned char**)(j+0x578),TRUE);
    original_photo_fog(job,lighting);
}

static BOOL photo_fog_change(BOOL install) {
    for(int attempt=0;attempt<3;attempt++) {
        GeometryThreads threads={0};
        if(!geometry_pause_threads(&photo_fog_patch,&threads)) {Sleep(1);continue;}
        BOOL result=geometry_exchange(&photo_fog_patch.sites[0],install);
        geometry_resume_threads(&threads);
        return result;
    }
    return FALSE;
}

static BOOL prepare_photo_fog(void) {
    static const unsigned char expected[8]={0xe8,0xeb,0x95,0xcf,0xff,0x4d,0x85,0xf6};
    static const unsigned char view_register[3]={0x48,0x8b,0xf9};
    unsigned char *site=(unsigned char*)(game_base+0x12bd0b0);
    if(photo_fog_patch.page)return InterlockedCompareExchange(&photo_fog_ready,0,0)!=0;
    if(memcmp(site,expected,8) || memcmp((void*)(game_base+0x12bce27),view_register,3))return FALSE;
    unsigned char *page=geometry_near_page(game_base,game_base+0x7155000);
    if(!page)return FALSE;
    /* Leaf tail relay: MOV R8,RDI supplies the caller's source-view pointer;
     * MOV RAX,hook; JMP RAX preserves the original CALL's return address.
     * No stack/nonvolatile changes and no extra call frame. */
    const unsigned char relay[5]={0x49,0x89,0xf8,0x48,0xb8};
    memcpy(page,relay,5);
    uintptr_t hook=(uintptr_t)HookPhotoPrepareFog;
    memcpy(page+5,&hook,8);page[13]=0xff;page[14]=0xe0;
    intptr_t relative=(intptr_t)page-(intptr_t)(site+5);
    if(relative<INT32_MIN || relative>INT32_MAX)goto fail;
    unsigned char replacement[8];memcpy(replacement,expected,8);
    int32_t displacement=(int32_t)relative;memcpy(replacement+1,&displacement,4);
    DWORD old;
    if(!VirtualProtect(page,4096,PAGE_EXECUTE_READ,&old) || !FlushInstructionCache(GetCurrentProcess(),page,15))goto fail;
    photo_fog_patch.page=page;
    GeometrySite *s=&photo_fog_patch.sites[0];s->site=site;s->relay=page;
    memcpy(&s->original,expected,8);memcpy(&s->replacement,replacement,8);
    original_photo_fog=(void(*)(void*,void*))(game_base+0xfb66a0);
    if(photo_fog_change(TRUE)) {InterlockedExchange(&photo_fog_ready,1);return TRUE;}
    /* An exceptional failed page/cache rollback may still leave the relay
     * reachable. Keep its page and transparent original callback alive. */
    if(s->changed)return FALSE;
    memset(&photo_fog_patch,0,sizeof(photo_fog_patch));
fail:
    VirtualFree(page,0,MEM_RELEASE);return FALSE;
}
#endif
