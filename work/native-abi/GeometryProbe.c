#include <stdio.h>
#include "GeometryLOD.h"
static volatile LONG gate;
static uint32_t observed;
static volatile LONG worker_stop,worker_bad;
static int (*worker_function)(void);
static HANDLE worker_ready;
static DWORD WINAPI renderer_worker(LPVOID unused) {
    (void)unused;
    for(int i=0;i<1000;i++)worker_function();
    SetEvent(worker_ready);
    while(!worker_stop) {
        int value=worker_function();if(value!=0 && value!=7)InterlockedExchange(&worker_bad,1);
    }
    return 0;
}

static unsigned char *make_function(unsigned char *p,int second,RUNTIME_FUNCTION *f,uintptr_t base) {
    unsigned char *begin=p;
    *p++=0x57;                               /* push rdi */
    unsigned char sub[]={0x48,0x81,0xec,0xe0,0,0,0};memcpy(p,sub,7);p+=7;
    unsigned char store[]={0xc7,0x84,0x24,0,0,0,0,0x27,0x43,0x05,0};
    store[3]=second?0x80:0xd8;memcpy(p,store,11);p+=11;
    *p++=0xbf;uint32_t five=5;memcpy(p,&five,4);p+=4;
    *p++=0xb8;uint32_t two=2;memcpy(p,&two,4);p+=4;
    while((uintptr_t)p&7)*p++=0x90;
    unsigned char *site=p;
    unsigned char window[]={0x03,0xf8,0x8b,0x84,0x24,0,0,0,0};
    window[5]=second?0x80:0xd8;memcpy(p,window,9);p+=9;
    *p++=0x23;*p++=0xf8;                    /* native AND: relay flags die */
    /* Record the value loaded by the displaced native MOV without touching EDI. */
    *p++=0x48;*p++=0xba;uintptr_t target=(uintptr_t)&observed;memcpy(p,&target,8);p+=8;
    *p++=0x89;*p++=0x02;
    *p++=0x89;*p++=0xf8;                     /* mov eax,edi */
    unsigned char add[]={0x48,0x81,0xc4,0xe0,0,0,0};memcpy(p,add,7);p+=7;
    *p++=0x5f;*p++=0xc3;
    unsigned char unwind[]={1,8,3,0,8,1,0x1c,0,1,0x70,0,0};
    memcpy(begin+128,unwind,sizeof(unwind));
    f->BeginAddress=(DWORD)((uintptr_t)begin-base);
    f->EndAddress=(DWORD)((uintptr_t)p-base);
    f->UnwindData=(DWORD)((uintptr_t)(begin+128)-base);
    return site;
}

static BOOL same_unwind(uintptr_t base,RUNTIME_FUNCTION *original,GeometryPatch *patch,int index) {
    uint64_t stack[96]={0};uintptr_t sp=(uintptr_t)&stack[8];
    *(uint64_t*)(sp+0xe0)=0x123456789;
    *(uint64_t*)(sp+0xe8)=0x765432100;
    CONTEXT native={0};native.ContextFlags=CONTEXT_FULL;native.Rsp=sp;native.Rdi=17;
    native.Rip=(DWORD64)(patch->sites[index].site+2);
    PVOID handler=NULL;DWORD64 establisher=0;
    RtlVirtualUnwind(UNW_FLAG_NHANDLER,base,native.Rip,original,&native,&handler,&establisher,NULL);
    const int boundaries[]={0,2,12,15,17,19,26,36};
    for(unsigned point=0;point<sizeof(boundaries)/sizeof(boundaries[0]);point++) {
        int offset=boundaries[point];
        CONTEXT relay={0};relay.ContextFlags=CONTEXT_FULL;relay.Rsp=sp;relay.Rdi=17;
        relay.Rip=(DWORD64)(patch->sites[index].relay+offset);
        DWORD64 dynamic_base=0;
        RUNTIME_FUNCTION *entry=RtlLookupFunctionEntry(relay.Rip,&dynamic_base,NULL);
        if(entry!=&patch->table[index] || dynamic_base!=base) {
            printf("lookup %d/%d entry=%p expected=%p base=%llx expected=%llx\n",index,offset,(void*)entry,(void*)&patch->table[index],(unsigned long long)dynamic_base,(unsigned long long)base);return FALSE;
        }
        RtlVirtualUnwind(UNW_FLAG_NHANDLER,dynamic_base,relay.Rip,entry,&relay,&handler,&establisher,NULL);
        if(relay.Rsp!=native.Rsp || relay.Rdi!=native.Rdi || relay.Rip!=native.Rip) {
            printf("unwind %d/%d rsp=%llx/%llx rdi=%llx/%llx rip=%llx/%llx\n",index,offset,(unsigned long long)relay.Rsp,(unsigned long long)native.Rsp,(unsigned long long)relay.Rdi,(unsigned long long)native.Rdi,(unsigned long long)relay.Rip,(unsigned long long)native.Rip);return FALSE;
        }
    }
    return native.Rdi==0x123456789 && native.Rip==0x765432100 && native.Rsp==sp+0xf0;
}

int main(void) {
    unsigned char *image=VirtualAlloc(NULL,65536,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
    if(!image)return 1;
    uintptr_t base=(uintptr_t)image;
    RUNTIME_FUNCTION original[2];
    unsigned char *a=make_function(image,0,&original[0],base);
    unsigned char *b=make_function(image+4096,1,&original[1],base);
    GeometryPatch p={0};
    unsigned char saved[2][9];memcpy(saved[0],a,9);memcpy(saved[1],b,9);
    a[0]=0x90;
    if(geometry_prepare(&p,base,base+65536,a,b,&gate,original) || p.page)return 2;
    memcpy(a,saved[0],9);
    a[9]=0x90;
    if(geometry_prepare(&p,base,base+65536,a,b,&gate,original) || p.page)return 18;
    a[9]=0x23;
    if(!geometry_prepare(&p,base,base+65536,a,b,&gate,original))return 3;
    if(!same_unwind(base,&original[0],&p,0) || !same_unwind(base,&original[1],&p,1))return 4;
    DWORD old;if(!VirtualProtect(image,65536,PAGE_EXECUTE_READ,&old))return 5;
    int (*functions[2])(void)={(int(*)(void))image,(int(*)(void))(image+4096)};
    for(int i=0;i<2;i++)if(functions[i]()!=7 || observed!=0x54327)return 6;
    worker_function=functions[0];worker_ready=CreateEventW(NULL,TRUE,FALSE,NULL);
    HANDLE worker=CreateThread(NULL,0,renderer_worker,NULL,0,NULL);
    if(!worker || WaitForSingleObject(worker_ready,5000)!=WAIT_OBJECT_0)return 15;
    if(!geometry_install(&p))return 7;
    for(int active=0;active<=2;active++) {
        InterlockedExchange(&gate,active);
        for(int i=0;i<2;i++)if(functions[i]()!=(active==1?0:7) || observed!=0x54327)return 8;
    }
    MEMORY_BASIC_INFORMATION info;
    if(!VirtualQuery(a,&info,sizeof(info)) || info.Protect!=PAGE_EXECUTE_READ)return 9;
    if(a[8]!=saved[0][8] || b[8]!=saved[1][8])return 10;
    if(!geometry_restore(&p) || memcmp(a,saved[0],9) || memcmp(b,saved[1],9))return 11;
    if(functions[0]()!=7 || functions[1]()!=7)return 12;
    for(int i=0;i<20;i++)if(!geometry_install(&p) || !geometry_restore(&p))return 16;
    InterlockedExchange(&worker_stop,1);
    if(WaitForSingleObject(worker,5000)!=WAIT_OBJECT_0 || worker_bad)return 17;
    CloseHandle(worker);CloseHandle(worker_ready);
    /* Refuse to overwrite a third-party conflict while rolling back site one. */
    if(!VirtualProtect(b,8,PAGE_EXECUTE_READWRITE,&old))return 13;
    b[0]=0x90;DWORD unused;VirtualProtect(b,8,old,&unused);
    if(geometry_install(&p) || memcmp(a,saved[0],9) || b[0]!=0x90)return 14;
    puts("PASS: exact/aligned guards, atomic eight-byte jumps, concurrent renderer pause/restore, native stack MOV, Photo gate, restore/conflict rollback, page protection, and chained unwind at every relay instruction boundary.");
    return 0;
}
