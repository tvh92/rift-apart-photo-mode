/* Real native light-filter cutoff window and relay; no game process opened.
 * Runs exact-build bytes 10B9BDD..10B9C41 (bit18 far cutoff, bit19 near fade)
 * with real helpers 10B9750/389950 through a harness that recreates the job
 * frame ([rsp+38h]=view+30, RBX=record, R8D=flags, XMM6=0, XMM8=1). */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <math.h>
#include "../../outputs/camera-native-lighting-v3/GeometryLOD.h"
static uintptr_t game_base;
static volatile LONG geometry_active;
#include "../../outputs/camera-native-lighting-v3/PhotoLight.h"
#include "../../outputs/camera-native-lighting-v3/PhotoCutoff.h"
#include "PhotoCutoffFixture.h"
typedef int (*FilterFn)(void *record,const void *camera,uint32_t flags,uint64_t *rax_out);
static void set_float(unsigned char *p,unsigned off,float value){memcpy(p+off,&value,4);}
static void put(uintptr_t at,const char *bytes,unsigned n){memcpy((void*)(game_base+at),bytes,n);}
static void put_jump(uintptr_t at,uintptr_t target){
    unsigned char *p=(unsigned char*)(game_base+at);p[0]=0xe9;
    int32_t d=(int32_t)((intptr_t)target-(intptr_t)(at+5));memcpy(p+1,&d,4);
}
static void build_harness(void) {
    /* Entry 10B9B00: push rbx; sub rsp,60h; save xmm6/xmm8; set frame; jmp 10B9BDD. */
    put(0x10b9b00,"\x53\x48\x83\xec\x60\x0f\x29\x74\x24\x40\x44\x0f\x29\x44\x24\x50"
                  "\x48\x89\xcb\x48\x89\x54\x24\x38\x4c\x89\x4c\x24\x28\x0f\x57\xf6"
                  "\xb8\x00\x00\x80\x3f\x66\x44\x0f\x6e\xc0\x48\x8b\x44\x24\x38",47);
    put_jump(0x10b9b00+47,0x10b9bdd);
    /* Epilogue 10B9B80: restore xmm6/xmm8, add rsp,60h; pop rbx; ret. */
    put(0x10b9b80,"\x0f\x28\x74\x24\x40\x44\x0f\x28\x44\x24\x50\x48\x83\xc4\x60\x5b\xc3",17);
    /* Keep landing 10B9C41 and drop landing 10B9C99 record RAX, return 1/0. */
    put(0x10b9c41,"\x48\x8b\x4c\x24\x28\x48\x89\x01\xb8\x01\x00\x00\x00",13);put_jump(0x10b9c41+13,0x10b9b80);
    put(0x10b9c99,"\x48\x8b\x4c\x24\x28\x48\x89\x01\x31\xc0",10);put_jump(0x10b9c99+10,0x10b9b80);
}
static unsigned char view[0x2080],other[0x2080];
static int run(FilterFn f,unsigned char *record,const unsigned char *v,uint32_t flags,BOOL *rax_ok) {
    uint64_t rax=0;int kept=f(record,v+0x30,flags,&rax);
    *rax_ok=rax==(uint64_t)(uintptr_t)(v+0x30);return kept;
}
static BOOL unwind_matches(uintptr_t pc,uintptr_t reference) {
    static unsigned char stack[0x800];
    for(unsigned i=0;i<sizeof(stack);i++)stack[i]=(unsigned char)(i*37+11);
    CONTEXT a={0},b={0};
    DWORD64 image=0,establisher=0;void *handler=NULL;
    a.Rsp=b.Rsp=(DWORD64)(uintptr_t)(stack+0x100);a.Rip=pc;b.Rip=reference;
    RUNTIME_FUNCTION *fa=RtlLookupFunctionEntry(pc,&image,NULL);
    if(!fa || image!=game_base)return FALSE;
    RtlVirtualUnwind(UNW_FLAG_NHANDLER,image,pc,fa,&a,&handler,&establisher,NULL);
    RUNTIME_FUNCTION *fb=RtlLookupFunctionEntry(reference,&image,NULL);
    if(!fb)return FALSE;
    RtlVirtualUnwind(UNW_FLAG_NHANDLER,image,reference,fb,&b,&handler,&establisher,NULL);
    return a.Rsp==b.Rsp && a.Rip==b.Rip && a.Rbx==b.Rbx && a.Rdi==b.Rdi && a.Rsi==b.Rsi &&
           a.R12==b.R12 && a.R13==b.R13 && a.R14==b.R14 && a.R15==b.R15 && a.Rbp==b.Rbp;
}
int main(void) {
    game_base=(uintptr_t)VirtualAlloc(NULL,0x7155000,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
    if(!game_base)return 1;
    fill_cutoff_fixture(game_base);build_harness();
    if(!RtlAddFunctionTable(cut_native_rows,CUT_NATIVE_ROWS,game_base))return 2;
    *(void**)(game_base+0x6739b10)=view;
    DWORD old;
    if(!VirtualProtect((void*)game_base,0x7155000,PAGE_EXECUTE_READ,&old))return 3;
    if(!VirtualProtect((void*)(game_base+0x6739000),4096,PAGE_READWRITE,&old))return 4;
    FlushInstructionCache(GetCurrentProcess(),(void*)game_base,0x7155000);
    FilterFn filter=(FilterFn)(game_base+0x10b9b00);
    unsigned char *site=(unsigned char*)(game_base+0x10b9c00);
    unsigned char window[16];memcpy(window,site,16);
    /* Guard refusals: changed site byte, changed preceding call window. */
    if(!VirtualProtect(site-0x12,0x22,PAGE_EXECUTE_READWRITE,&old))return 5;
    site[8]=0x86;
    if(prepare_photo_cutoff() || photo_cutoff_patch.page)return 6;
    site[8]=0x87;site[-5]=0x90;
    if(prepare_photo_cutoff() || photo_cutoff_patch.page)return 7;
    site[-5]=0xe8;VirtualProtect(site-0x12,0x22,old,&old);
    FlushInstructionCache(GetCurrentProcess(),site-0x12,0x22);
    /* Native reference results before installation. */
    unsigned char record[0x170]={0},before[0x170];
    set_float(record,0,1);set_float(record,0x14,1);set_float(record,0x28,1);
    set_float(record,0x70,1);set_float(record,0x74,1);set_float(record,0x78,1);
    set_float(record,0xa0,150);
    const float distances[]={0,50,140,149.5f,150.5f,160,300,2000},radii[]={0,15.05f};
    const float near_offset[]={1,-0.5f};
    int native_far[2][2][2][8],native_plain[2][2][2][8];BOOL rax_ok;
    for(unsigned r=0;r<2;r++)for(unsigned n=0;n<2;n++)for(unsigned b19=0;b19<2;b19++)for(unsigned i=0;i<8;i++) {
        set_float(record,0x4c,radii[r]);set_float(record,0x30,distances[i]);
        set_float(record,0x98,near_offset[n]);set_float(record,0x9c,.001f);
        for(unsigned b18=0;b18<2;b18++) {
            uint32_t flags=(b18<<18)|(b19<<19);
            int kept=run(filter,record,view,flags,&rax_ok);
            if(!rax_ok)return 8;
            if(b18)native_far[r][n][b19][i]=kept; else native_plain[r][n][b19][i]=kept;
        }
    }
    /* Sanity: the native bit18 cutoff drops beyond 150 front distance. */
    if(native_far[0][0][0][4]!=0 || native_far[0][0][0][3]!=1 || native_plain[0][0][0][7]!=1)return 9;
    if(native_far[1][0][0][5]!=1 || native_far[1][0][0][6]!=0)return 10;
    if(!prepare_photo_cutoff()) {
        printf("Cutoff guard window:");for(unsigned i=0;i<16;i++)printf(" %02x",site[i]);puts("");return 11;
    }
    if(photo_cutoff_relay_size!=112)return 12;
    if(memcmp(site+8,window+8,8) || site[0]!=0xe9 || site[5]!=0x90 || site[6]!=0x90 || site[7]!=0x90)return 13;
    unsigned cases=0;LONG expected_hits=0;
    for(unsigned r=0;r<2;r++)for(unsigned n=0;n<2;n++)for(unsigned b19=0;b19<2;b19++)for(unsigned i=0;i<8;i++) {
        set_float(record,0x4c,radii[r]);set_float(record,0x30,distances[i]);
        set_float(record,0x98,near_offset[n]);set_float(record,0x9c,.001f);
        uint32_t far_flags=(1u<<18)|(b19<<19),plain=b19<<19;
        memcpy(before,record,sizeof(before));
        geometry_active=1;
        if(run(filter,record,view,far_flags,&rax_ok)!=native_plain[r][n][b19][i] || !rax_ok)return 14;
        expected_hits++;
        if(run(filter,record,view,plain,&rax_ok)!=native_plain[r][n][b19][i] || !rax_ok)return 15;
        if(run(filter,record,other,far_flags,&rax_ok)!=native_far[r][n][b19][i] || !rax_ok)return 16;
        geometry_active=0;
        if(run(filter,record,view,far_flags,&rax_ok)!=native_far[r][n][b19][i] || !rax_ok)return 17;
        geometry_active=1;photo_cutoff_ready=0;
        if(run(filter,record,view,far_flags,&rax_ok)!=native_far[r][n][b19][i] || !rax_ok)return 18;
        photo_cutoff_ready=1;
        if(memcmp(record,before,sizeof(before)))return 19;
        cases++;
    }
    if(photo_cutoff_hits!=expected_hits)return 20;
    /* Bridge example: lamp A0=150, front distance 155.8 -> native drop, Photo keep. */
    set_float(record,0x4c,15.05f);set_float(record,0x30,170.85f);set_float(record,0x98,1);
    int photo_keep=run(filter,record,view,1u<<18,&rax_ok);
    geometry_active=0;int off_keep=run(filter,record,view,1u<<18,&rax_ok);geometry_active=1;
    if(off_keep!=0 || photo_keep!=1)return 21;
    printf("Bridge lamp example (A0=150, front 155.8): Ctrl off kept=%d, Photo/Ctrl kept=%d.\n",off_keep,photo_keep);
    /* Unwind: every relay instruction start must unwind like the native site. */
    static const unsigned starts[]={0,10,13,19,29,32,38,48,51,55,60,66,76,79,84,89,94,101,107};
    for(unsigned i=0;i<sizeof(starts)/sizeof(starts[0]);i++)
        if(!unwind_matches((uintptr_t)photo_cutoff_patch.page+starts[i],(uintptr_t)site))return 22;
    /* Atomic restoration and post-restore native behaviour. */
    if(!photo_cutoff_change(FALSE) || memcmp(site,window,16))return 23;
    set_float(record,0x4c,0);set_float(record,0x30,160);
    if(run(filter,record,view,1u<<18,&rax_ok)!=0 || !rax_ok)return 24;
    if(!photo_cutoff_change(TRUE) || site[0]!=0xe9)return 25;
    printf("PhotoCutoffProbe passed: %u native filter cases x5 gates, RAX/source preservation, exact site/call guards, ready/Ctrl/auxiliary-view gates, %u relay unwind starts, adjacent bytes, atomic restore/reinstall.\n",cases,(unsigned)(sizeof(starts)/sizeof(starts[0])));
    return 0;
}
