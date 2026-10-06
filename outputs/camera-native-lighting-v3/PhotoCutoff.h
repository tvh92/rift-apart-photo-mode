/* Pre-upload far cutoff in light filter job 10B9A50. With bit18 set it drops a
 * light whose front-of-bounds distance exceeds rec+A0 (10B9C00 comiss, 10B9C07
 * ja). The RGB/specular fades already ignore bit18 for primary Photo/Ctrl, so
 * this earlier drop is what made lamps blip off. The leaf relay keeps those
 * lights for the primary Photo view only; otherwise it replays the original
 * compare/branch. Source records and flags never change. */
#ifndef PHOTO_CUTOFF_H
#define PHOTO_CUTOFF_H
static GeometryPatch photo_cutoff_patch;
static volatile LONG photo_cutoff_ready;
static volatile LONG photo_cutoff_hits;
static unsigned photo_cutoff_relay_size;

static BOOL photo_cutoff_change(BOOL install) {
    if(!photo_cutoff_patch.registered)return FALSE;
    for(int attempt=0;attempt<3;attempt++) {
        GeometryThreads threads={0};
        if(!geometry_pause_threads(&photo_cutoff_patch,&threads)){Sleep(1);continue;}
        BOOL result=geometry_exchange(&photo_cutoff_patch.sites[0],install);
        geometry_resume_threads(&threads);return result;
    }
    return FALSE;
}
static unsigned char *cutoff_emit_jump(unsigned char **p,unsigned char opcode) {
    if(opcode==0xe9)*(*p)++=0xe9; else {*(*p)++=0x0f;*(*p)++=opcode;}
    unsigned char *disp=*p;memset(*p,0,4);*p+=4;return disp;
}
static BOOL cutoff_target(unsigned char *disp,uintptr_t target) {
    intptr_t delta=(intptr_t)target-(intptr_t)(disp+4);
    if(delta<INT32_MIN || delta>INT32_MAX)return FALSE;
    int32_t relative=(int32_t)delta;memcpy(disp,&relative,4);return TRUE;
}
static BOOL prepare_photo_cutoff(void) {
    /* 10B9C00: comiss xmm0,[rbx+A0h] ; first byte of ja near 10B9C99. */
    static const unsigned char expected[16]={0x0f,0x2f,0x83,0xa0,0,0,0,0x0f,0x87,0x8c,0,0,0,0x41,0xc1,0xe8};
    /* 10B9BEE..10B9BFB: rax=[rsp+38h] (view+30), call 10B9750(rec,camera). */
    static const unsigned char before[18]={0x48,0x8b,0x44,0x24,0x38,0x74,0x18,0x48,0x8b,0xd0,0x48,0x8b,0xcb,0xe8,0x50,0xfb,0xff,0xff};
    unsigned char *site=(unsigned char*)(game_base+0x10b9c00);
    if(photo_cutoff_patch.page)return InterlockedCompareExchange(&photo_cutoff_ready,0,0)!=0;
    if(memcmp(site,expected,sizeof(expected)) || memcmp(site-0x12,before,sizeof(before)))return FALSE;
    DWORD64 image=0;
    RUNTIME_FUNCTION *native=RtlLookupFunctionEntry((DWORD64)site,&image,NULL);
    if(!native || image!=game_base || native->BeginAddress!=0x10b9aed || native->EndAddress!=0x10b9d48)return FALSE;
    unsigned char *unwind=(unsigned char*)(game_base+native->UnwindData);
    if(unwind[0]!=0x21)return FALSE; /* v1 CHAININFO, no language handler */
    unsigned char *page=geometry_near_page(game_base,game_base+0x7155000);
    if(!page)return FALSE;
    unsigned char *p=page,*replay_jumps[3],*keep,*drop,*resume;
    light_emit_address(&p,0x48,0xb8,(uintptr_t)&photo_cutoff_ready);
    memcpy(p,"\x83\x38\x01",3);p+=3;replay_jumps[0]=cutoff_emit_jump(&p,0x85);
    light_emit_address(&p,0x48,0xb8,(uintptr_t)&geometry_active);
    memcpy(p,"\x83\x38\x01",3);p+=3;replay_jumps[1]=cutoff_emit_jump(&p,0x85);
    /* Job context +48 is the view; [rsp+38h] holds view+30 (10B9A92..10B9AA1). */
    light_emit_address(&p,0x48,0xb8,game_base+0x6739b10);
    memcpy(p,"\x48\x8b\x00\x48\x83\xc0\x30\x48\x3b\x44\x24\x38",12);p+=12;
    replay_jumps[2]=cutoff_emit_jump(&p,0x85);
    light_emit_address(&p,0x48,0xb8,(uintptr_t)&photo_cutoff_hits);
    memcpy(p,"\xf0\xff\x00",3);p+=3; /* diagnostic counter; no renderer logging */
    /* 10B9750 never writes RAX, so native RAX here equals [rsp+38h]. */
    memcpy(p,"\x48\x8b\x44\x24\x38",5);p+=5;keep=cutoff_emit_jump(&p,0xe9);
    unsigned char *replay=p;
    memcpy(p,"\x48\x8b\x44\x24\x38",5);p+=5;
    memcpy(p,expected,7);p+=7; /* original comiss */
    drop=cutoff_emit_jump(&p,0x87);resume=cutoff_emit_jump(&p,0xe9);
    for(unsigned i=0;i<3;i++){int32_t d=(int32_t)(replay-(replay_jumps[i]+4));memcpy(replay_jumps[i],&d,4);}
    /* Flags are overwritten by SHR at 10B9C0D before any consumption. */
    if(!cutoff_target(keep,game_base+0x10b9c0d) || !cutoff_target(drop,game_base+0x10b9c99) ||
       !cutoff_target(resume,game_base+0x10b9c0d))goto fail;
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
    photo_cutoff_patch.page=page;photo_cutoff_patch.table=table;photo_cutoff_patch.registered=TRUE;
    photo_cutoff_relay_size=(unsigned)(p-page);
    GeometrySite *s=&photo_cutoff_patch.sites[0];s->site=site;s->relay=page;
    /* Only the aligned word 10B9C00..07 changes; 10B9C05..0C are never
     * reached after the JMP and no branch targets 10B9C01..10B9C0C. */
    unsigned char replacement[8]={0xe9,0,0,0,0,0x90,0x90,0x90};
    int32_t relative=(int32_t)delta;memcpy(replacement+1,&relative,4);
    memcpy(&s->original,expected,8);memcpy(&s->replacement,replacement,8);
    if(photo_cutoff_change(TRUE)){InterlockedExchange(&photo_cutoff_ready,1);return TRUE;}
    /* Preserve any exceptionally reachable relay and its unwind entry. */
    if(s->changed)return FALSE;
    RtlDeleteFunctionTable(table);memset(&photo_cutoff_patch,0,sizeof(photo_cutoff_patch));
fail:
    VirtualFree(page,0,MEM_RELEASE);return FALSE;
}
#endif
