/* Type4 stores a separate camera-faded specular multiplier. Retain its native
 * near fade using a private source copy; no source writes or escaped copies. */
#ifndef PHOTO_SPECULAR_H
#define PHOTO_SPECULAR_H
static GeometryPatch photo_specular_patch;
static volatile LONG photo_specular_ready;
static float (*original_photo_specular)(const void*,const void*);
static float HookPhotoType4Specular(const void *light,const void *view) {
    if(InterlockedCompareExchange(&photo_specular_ready,0,0) &&
       InterlockedCompareExchange(&geometry_active,0,0) && view &&
       (uintptr_t)view==*(uintptr_t*)(game_base+0x6739b10)) {
        /* Exact helper reads only transform/bounds/flags/fade up to A4. Its
         * only nested call is a distance calculation; no pointers escape. */
        unsigned char copy[0xb0];memcpy(copy,light,sizeof(copy));
        uint32_t flags;memcpy(&flags,copy+0x88,4);flags&=~(1u<<18);memcpy(copy+0x88,&flags,4);
        InterlockedIncrement(&photo_light_hits);
        return original_photo_specular(copy,view);
    }
    return original_photo_specular(light,view);
}
static BOOL photo_specular_change(BOOL install) {
    for(int attempt=0;attempt<3;attempt++) {
        GeometryThreads threads={0};
        if(!geometry_pause_threads(&photo_specular_patch,&threads)){Sleep(1);continue;}
        BOOL result=geometry_exchange(&photo_specular_patch.sites[0],install);
        geometry_resume_threads(&threads);return result;
    }
    return FALSE;
}
static BOOL prepare_photo_specular(void) {
    const unsigned char expected[8]={0x78,0xe8,0x2a,0xad,0xfd,0xff,0xf3,0x0f};
    const unsigned char prolog[12]={0x40,0x53,0x48,0x83,0xec,0x60,0x8b,0x81,0x88,0,0,0};
    unsigned char *site=(unsigned char*)(game_base+0x10be260);
    if(photo_specular_patch.page)return InterlockedCompareExchange(&photo_specular_ready,0,0)!=0;
    if(memcmp(site,expected,8) || memcmp((void*)(game_base+0x1098f90),prolog,sizeof(prolog)))return FALSE;
    unsigned char *page=geometry_near_page(game_base,game_base+0x7155000);
    if(!page)return FALSE;
    page[0]=0x48;page[1]=0xb8;uintptr_t hook=(uintptr_t)HookPhotoType4Specular;
    memcpy(page+2,&hook,8);page[10]=0xff;page[11]=0xe0;
    intptr_t delta=(intptr_t)page-(intptr_t)(site+6);
    if(delta<INT32_MIN || delta>INT32_MAX)goto fail;
    unsigned char replacement[8];memcpy(replacement,expected,8);
    int32_t relative=(int32_t)delta;memcpy(replacement+2,&relative,4);
    DWORD old;
    if(!VirtualProtect(page,4096,PAGE_EXECUTE_READ,&old) || !FlushInstructionCache(GetCurrentProcess(),page,12))goto fail;
    /* Leaf tail relay changes no stack/nonvolatile state. Only the existing
     * CALL displacement changes, within one aligned atomic word. Adjacent
     * operand/instruction-prefix bytes are preserved exactly. */
    photo_specular_patch.page=page;
    GeometrySite *s=&photo_specular_patch.sites[0];s->site=site;s->relay=page;
    memcpy(&s->original,expected,8);memcpy(&s->replacement,replacement,8);
    original_photo_specular=(float(*)(const void*,const void*))(game_base+0x1098f90);
    if(photo_specular_change(TRUE)){InterlockedExchange(&photo_specular_ready,1);return TRUE;}
    if(s->changed)return FALSE;
    memset(&photo_specular_patch,0,sizeof(photo_specular_patch));
fail:
    VirtualFree(page,0,MEM_RELEASE);return FALSE;
}
#endif
