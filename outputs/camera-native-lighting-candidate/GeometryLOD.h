/* Prototype: native geometry tier preference, retaining masks/resource floors.
 * The caller supplies a validated Photo lifecycle gate. No view/global scale
 * values are modified. Supported sites are aligned, atomically patched words.
 */
#ifndef PHOTO_GEOMETRY_LOD_H
#define PHOTO_GEOMETRY_LOD_H
#include <windows.h>
#include <tlhelp32.h>
#include <stdint.h>
#include <string.h>

typedef struct {
    unsigned char *site,*relay;
    uint64_t original,replacement;
    BOOL changed;
} GeometrySite;
typedef struct {
    GeometrySite sites[2];
    unsigned char *page;
    RUNTIME_FUNCTION *table;
    BOOL registered;
} GeometryPatch;

typedef struct {HANDLE handles[256];unsigned count,suspended;} GeometryThreads;
static void geometry_resume_threads(GeometryThreads *threads) {
    for(unsigned i=0;i<threads->suspended;i++)ResumeThread(threads->handles[i]);
    for(unsigned i=0;i<threads->count;i++)CloseHandle(threads->handles[i]);
    memset(threads,0,sizeof(*threads));
}
static BOOL geometry_pause_threads(GeometryPatch *patch,GeometryThreads *threads) {
    /* Atomically replacing two instructions still needs thread coordination:
     * a thread between ADD and MOV must finish that window first. Prepare all
     * resources BEFORE suspension, and do no allocation/logging while paused. */
    DWORD current=GetCurrentThreadId(),process=GetCurrentProcessId();
    HANDLE snapshot=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);
    if(snapshot==INVALID_HANDLE_VALUE)return FALSE;
    THREADENTRY32 entry={0};entry.dwSize=sizeof(entry);
    BOOL ok=Thread32First(snapshot,&entry);
    if(!ok) {CloseHandle(snapshot);return FALSE;}
    do {
        if(entry.th32OwnerProcessID==process && entry.th32ThreadID!=current) {
            if(threads->count==256) {ok=FALSE;break;}
            HANDLE h=OpenThread(THREAD_SUSPEND_RESUME|THREAD_GET_CONTEXT,FALSE,entry.th32ThreadID);
            if(!h) {ok=FALSE;break;}
            threads->handles[threads->count++]=h;
        }
        entry.dwSize=sizeof(entry);
    } while(Thread32Next(snapshot,&entry));
    CloseHandle(snapshot);
    if(!ok) {geometry_resume_threads(threads);return FALSE;}
    for(unsigned i=0;i<threads->count;i++) {
        if(SuspendThread(threads->handles[i])==(DWORD)-1) {geometry_resume_threads(threads);return FALSE;}
        threads->suspended++;
        CONTEXT context={0};context.ContextFlags=CONTEXT_CONTROL;
        if(!GetThreadContext(threads->handles[i],&context)) {geometry_resume_threads(threads);return FALSE;}
        for(int j=0;j<2;j++) {
            uintptr_t site=(uintptr_t)patch->sites[j].site;
            if(context.Rip>=site && context.Rip<site+9) {geometry_resume_threads(threads);return FALSE;}
        }
    }
    return TRUE;
}

static BOOL geometry_exchange(GeometrySite *s,BOOL install) {
    DWORD old,unused;
    if(s->changed==install)return TRUE;
    if(!VirtualProtect(s->site,8,PAGE_EXECUTE_READWRITE,&old))return FALSE;
    LONG64 expected=(LONG64)(install?s->original:s->replacement);
    LONG64 desired=(LONG64)(install?s->replacement:s->original);
    LONG64 prior=InterlockedCompareExchange64((volatile LONG64*)s->site,desired,expected);
    BOOL protected_again=VirtualProtect(s->site,8,old,&unused);
    BOOL flushed=FlushInstructionCache(GetCurrentProcess(),s->site,8);
    if(prior==expected)s->changed=install;
    if(prior==expected && (!protected_again || !flushed)) {
        DWORD rollback_old;
        if(VirtualProtect(s->site,8,PAGE_EXECUTE_READWRITE,&rollback_old)) {
            LONG64 rollback=InterlockedCompareExchange64((volatile LONG64*)s->site,expected,desired);
            if(rollback==desired)s->changed=!install;
            VirtualProtect(s->site,8,old,&unused);
            FlushInstructionCache(GetCurrentProcess(),s->site,8);
        }
    }
    return prior==expected && protected_again && flushed;
}

static unsigned char *geometry_near_page(uintptr_t base,uintptr_t start) {
    /* Above the image so dynamically registered unwind ranges do not overlap
     * the module. Keep RVAs positive and both rel32 displacements in range. */
    uintptr_t cursor=(start+0xffff)&~(uintptr_t)0xffff;
    uintptr_t limit=base+0x70000000;
    while(cursor<limit) {
        MEMORY_BASIC_INFORMATION info;
        if(!VirtualQuery((void*)cursor,&info,sizeof(info)))return NULL;
        uintptr_t end=(uintptr_t)info.BaseAddress+info.RegionSize;
        if(info.State==MEM_FREE && end-cursor>=4096) {
            unsigned char *p=VirtualAlloc((void*)cursor,4096,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
            if(p)return p;
        }
        if(end<=cursor)return NULL;
        cursor=(end+0xffff)&~(uintptr_t)0xffff;
    }
    return NULL;
}

static BOOL geometry_prepare(GeometryPatch *patch,uintptr_t base,uintptr_t image_end,
        unsigned char *first,unsigned char *second,volatile LONG *active,
        const RUNTIME_FUNCTION original_functions[2]) {
    const unsigned char guards[2][9]={
        {0x03,0xf8,0x8b,0x84,0x24,0xd8,0x00,0x00,0x00},
        {0x03,0xf8,0x8b,0x84,0x24,0x80,0x00,0x00,0x00}};
    unsigned char *sites[2]={first,second};
    if(patch->page || !active)return FALSE;
    for(int i=0;i<2;i++) {
        /* Both continuations immediately AND EDI,EAX. It overwrites flags
         * before any consumer, so the relay's CMP/XOR flags are dead. */
        if(((uintptr_t)sites[i]&7) || memcmp(sites[i],guards[i],9) ||
           sites[i][9]!=0x23 || sites[i][10]!=0xf8)return FALSE;
        /* Original selectors have v1 unwind metadata without an EH handler.
         * Chain to it rather than cloning an original function/EH frame. */
        unsigned char *unwind=(unsigned char*)(base+original_functions[i].UnwindData);
        if(unwind[0]!=1 || unwind[3]!=0)return FALSE;
    }
    unsigned char *page=geometry_near_page(base,image_end);
    if(!page)return FALSE;
    patch->page=page;patch->table=(RUNTIME_FUNCTION*)(page+256);
    for(int i=0;i<2;i++) {
        GeometrySite *s=&patch->sites[i];
        s->site=sites[i];s->relay=page+64*i;
        unsigned char *p=s->relay;
        /* EAX is scratch only AFTER its native contribution to EDI. R11 is
         * dead at both native continuations (next use sets it, or no use).
         * No stack changes or calls; real distances and XMMs survive. */
        *p++=0x03;*p++=0xf8;                    /* add edi,eax */
        *p++=0x48;*p++=0xb8;
        uintptr_t gate=(uintptr_t)active;memcpy(p,&gate,8);p+=8;
        *p++=0x83;*p++=0x38;*p++=0x01;          /* cmp dword [rax],1 */
        *p++=0x75;*p++=0x02;                    /* jne +2 */
        *p++=0x31;*p++=0xff;                    /* xor edi,edi */
        memcpy(p,guards[i]+2,7);p+=7;           /* mov eax,[rsp+...] */
        /* A mod=00 indirect JMP looks like a Windows epilog. Use R11's mod=11
         * register JMP so virtual unwind uses the chained native frame. */
        *p++=0x49;*p++=0xbb;
        uintptr_t continuation=(uintptr_t)s->site+9;memcpy(p,&continuation,8);p+=8;
        *p++=0x41;*p++=0xff;*p++=0xe3;
        uintptr_t displacement=(uintptr_t)s->relay-((uintptr_t)s->site+5);
        int64_t signed_displacement=(int64_t)displacement;
        if(signed_displacement<INT32_MIN || signed_displacement>INT32_MAX)goto fail;
        unsigned char replacement[8]={0xe9,0,0,0,0,0x90,0x90,0x90};
        int32_t relative=(int32_t)signed_displacement;memcpy(replacement+1,&relative,4);
        memcpy(&s->original,s->site,8);memcpy(&s->replacement,replacement,8);
        /* Native frame is already past every prolog save. The chained entry
         * describes that SAME frame; these relays create no additional frame. */
        unsigned char *chain=page+160+32*i;
        chain[0]=0x21;chain[1]=chain[2]=chain[3]=0;
        memcpy(chain+4,&original_functions[i],sizeof(RUNTIME_FUNCTION));
        patch->table[i].BeginAddress=(DWORD)((uintptr_t)s->relay-base);
        patch->table[i].EndAddress=(DWORD)((uintptr_t)p-base);
        patch->table[i].UnwindData=(DWORD)((uintptr_t)chain-base);
    }
    DWORD old;
    if(!VirtualProtect(page,4096,PAGE_EXECUTE_READ,&old) ||
       !FlushInstructionCache(GetCurrentProcess(),page,4096))goto fail;
    if(!RtlAddFunctionTable(patch->table,2,(DWORD64)base))goto fail;
    patch->registered=TRUE;
    return TRUE;
fail:
    VirtualFree(page,0,MEM_RELEASE);memset(patch,0,sizeof(*patch));return FALSE;
}

static BOOL geometry_change(GeometryPatch *patch,BOOL install) {
    if(!patch->registered)return FALSE;
    for(int attempt=0;attempt<16;attempt++) {
        GeometryThreads threads={0};
        if(!geometry_pause_threads(patch,&threads)) {Sleep(1);continue;}
        BOOL a=geometry_exchange(&patch->sites[0],install);
        BOOL b=a && geometry_exchange(&patch->sites[1],install);
        if(install && a && !b)geometry_exchange(&patch->sites[0],FALSE);
        if(!install && !a)b=geometry_exchange(&patch->sites[1],FALSE);
        geometry_resume_threads(&threads);
        return a && b;
    }
    return FALSE;
}
static BOOL geometry_install(GeometryPatch *patch) {return geometry_change(patch,TRUE);}

static BOOL geometry_restore(GeometryPatch *patch) {
    /* Keep relays and unwind entries for the process lifetime: another thread
     * could already be inside one even after the original bytes are restored. */
    return geometry_change(patch,FALSE);
}
#endif
