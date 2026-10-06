/* Exact-build ordinary-light colour fade override. The leaf relay changes
 * only the helper's local EDX flag copy, for proven primary Photo callers. */
#ifndef PHOTO_LIGHT_H
#define PHOTO_LIGHT_H
static GeometryPatch photo_light_patch;
static volatile LONG photo_light_ready;
static volatile LONG photo_light_hits;
static unsigned photo_light_relay_size;

static void light_emit_address(unsigned char **p,unsigned char prefix,unsigned char opcode,uintptr_t address) {
    *(*p)++=prefix;*(*p)++=opcode;memcpy(*p,&address,8);*p+=8;
}
static unsigned char *light_emit_branch(unsigned char **p,unsigned char opcode) {
    *(*p)++=0x0f;*(*p)++=opcode;unsigned char *disp=*p;memset(*p,0,4);*p+=4;return disp;
}
static void light_branch_target(unsigned char *disp,unsigned char *target) {
    int32_t delta=(int32_t)(target-(disp+4));memcpy(disp,&delta,4);
}
static BOOL photo_light_change(BOOL install) {
    if(!photo_light_patch.registered)return FALSE;
    for(int attempt=0;attempt<3;attempt++) {
        GeometryThreads threads={0};
        if(!geometry_pause_threads(&photo_light_patch,&threads)){Sleep(1);continue;}
        BOOL result=geometry_exchange(&photo_light_patch.sites[0],install);
        geometry_resume_threads(&threads);return result;
    }
    return FALSE;
}
static BOOL prepare_photo_light(void) {
    static const unsigned char expected[8]={0xf2,0x0f,0x10,0x81,0xa8,0,0,0};
    static const DWORD calls[4]={0x10be322,0x10be3ed,0x10be519,0x10be6c0};
    unsigned char *site=(unsigned char*)(game_base+0x1099270);
    if(photo_light_patch.page)return InterlockedCompareExchange(&photo_light_ready,0,0)!=0;
    if(memcmp(site,expected,8) || memcmp((void*)(game_base+0x10be1bf),"\x4c\x8b\xf1",3))return FALSE;
    for(unsigned i=0;i<4;i++) {
        unsigned char *call=(unsigned char*)(game_base+calls[i]);int32_t displacement;
        memcpy(&displacement,call+1,4);
        if(call[0]!=0xe8 || (uintptr_t)(call+5+displacement)!=game_base+0x1099200)return FALSE;
    }
    DWORD64 image=0;
    RUNTIME_FUNCTION *native=RtlLookupFunctionEntry((DWORD64)site,&image,NULL);
    if(!native || image!=game_base || native->BeginAddress!=0x1099243 || native->EndAddress!=0x10992cf)return FALSE;
    unsigned char *unwind=(unsigned char*)(game_base+native->UnwindData);
    if(unwind[0]!=0x21)return FALSE; /* v1 CHAININFO, no language handler */
    unsigned char *page=geometry_near_page(game_base,game_base+0x7155000);
    if(!page)return FALSE;
    unsigned char *p=page,*skip[4],*matched[4];
    light_emit_address(&p,0x48,0xb8,(uintptr_t)&photo_light_ready);
    memcpy(p,"\x83\x38\x01",3);p+=3;skip[0]=light_emit_branch(&p,0x85);
    light_emit_address(&p,0x48,0xb8,(uintptr_t)&geometry_active);
    memcpy(p,"\x83\x38\x01",3);p+=3;skip[1]=light_emit_branch(&p,0x85);
    /* The native prolog allocated A8 bytes; saved return PC is above that.
     * Restrict R14's interpretation to the four verified LightSubmit calls. */
    memcpy(p,"\x48\x8b\x84\x24\xa8\x00\x00\x00",8);p+=8;
    for(unsigned i=0;i<4;i++) {
        light_emit_address(&p,0x49,0xba,game_base+calls[i]+5);
        memcpy(p,"\x4c\x39\xd0",3);p+=3;matched[i]=light_emit_branch(&p,0x84);
    }
    skip[2]=light_emit_branch(&p,0x85); /* last comparison is unequal */
    unsigned char *view_check=p;
    light_emit_address(&p,0x48,0xb8,game_base+0x6739b10);
    memcpy(p,"\x4c\x3b\x30",3);p+=3;skip[3]=light_emit_branch(&p,0x85);
    memcpy(p,"\x81\xe2\xff\xff\xeb\xff",6);p+=6; /* clear local far-RGB bit18 and far-specular bit20 */
    light_emit_address(&p,0x48,0xb8,(uintptr_t)&photo_light_hits);
    memcpy(p,"\xf0\xff\x00",3);p+=3; /* diagnostic counter; no renderer logging */
    unsigned char *replay=p;
    memcpy(p,expected,8);p+=8;
    /* RAX is overwritten by native MOV EAX at 109927B; R10 is unused by this
     * helper. Flags are overwritten by TEST at 10992AD before consumption. */
    light_emit_address(&p,0x48,0xb8,(uintptr_t)site+8);
    *p++=0xff;*p++=0xe0;
    for(unsigned i=0;i<4;i++){light_branch_target(skip[i],replay);light_branch_target(matched[i],view_check);}
    unsigned char *chain=page+256;
    chain[0]=0x21;chain[1]=chain[2]=chain[3]=0;memcpy(chain+4,native,sizeof(*native));
    RUNTIME_FUNCTION *table=(RUNTIME_FUNCTION*)(page+288);
    table->BeginAddress=(DWORD)((uintptr_t)page-game_base);
    table->EndAddress=(DWORD)((uintptr_t)p-game_base);
    table->UnwindData=(DWORD)((uintptr_t)chain-game_base);
    intptr_t delta=(intptr_t)page-(intptr_t)(site+5);
    if(delta<INT32_MIN || delta>INT32_MAX)goto fail;
    DWORD old;
    if(!VirtualProtect(page,4096,PAGE_EXECUTE_READ,&old) || !FlushInstructionCache(GetCurrentProcess(),page,4096))goto fail;
    if(!RtlAddFunctionTable(table,1,(DWORD64)game_base))goto fail;
    photo_light_patch.page=page;photo_light_patch.table=table;photo_light_patch.registered=TRUE;
    photo_light_relay_size=(unsigned)(p-page);
    GeometrySite *s=&photo_light_patch.sites[0];s->site=site;s->relay=page;
    unsigned char replacement[8]={0xe9,0,0,0,0,0x90,0x90,0x90};
    int32_t relative=(int32_t)delta;memcpy(replacement+1,&relative,4);
    memcpy(&s->original,expected,8);memcpy(&s->replacement,replacement,8);
    if(photo_light_change(TRUE)){InterlockedExchange(&photo_light_ready,1);return TRUE;}
    /* Preserve any exceptionally reachable relay and its unwind entry. */
    if(s->changed)return FALSE;
    RtlDeleteFunctionTable(table);memset(&photo_light_patch,0,sizeof(photo_light_patch));
fail:
    VirtualFree(page,0,MEM_RELEASE);return FALSE;
}
#endif
