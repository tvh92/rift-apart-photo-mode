/* Executes the real native helper and production relay in this process only. */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <math.h>
#include "../../outputs/camera-native-lighting-v2/GeometryLOD.h"
static uintptr_t game_base;
static volatile LONG geometry_active;
#include "../../outputs/camera-native-lighting-v2/PhotoLight.h"
#include "PhotoLightFixture.h"
typedef void (*LightFn)(void*,float,float,float*,float*,unsigned*);
typedef void (*InvokeFn)(void*,float,float,float*,float*,unsigned*,void*);
static unsigned cases;
static void set_float(unsigned char *p,unsigned off,float value){memcpy(p+off,&value,4);}
static BOOL same(float a,float b){return fabsf(a-b)<0.000002f;}
static unsigned relay_instruction_size(const unsigned char *p) {
    if((p[0]==0x48 && p[1]==0xb8) || (p[0]==0x49 && p[1]==0xba))return 10;
    if(p[0]==0x83 && p[1]==0x38 && p[2]==1)return 3;
    if(p[0]==0x0f && (p[1]==0x84 || p[1]==0x85))return 6;
    if(!memcmp(p,"\x48\x8b\x84\x24",4))return 8;
    if(!memcmp(p,"\x4c\x39\xd0",3) || !memcmp(p,"\x4c\x3b\x30",3))return 3;
    if(p[0]==0x81 && p[1]==0xe2)return 6;
    if(!memcmp(p,"\xf0\xff\x00",3))return 3;
    if(!memcmp(p,"\xf2\x0f\x10\x81",4))return 8;
    if(p[0]==0xff && p[1]==0xe0)return 2;
    return 0;
}
static BOOL evaluate(InvokeFn fn,unsigned char *light,unsigned flags,float front,float centre,void *view,float *out) {
    unsigned char before[0x170];*(unsigned*)(light+0x88)=flags;memcpy(before,light,sizeof(before));
    unsigned kind=99;fn(light,front,centre,out,out+3,&kind,view);out[4]=(float)kind;
    return !memcmp(light,before,sizeof(before));
}
static BOOL compare_unwind(uintptr_t pc) {
    unsigned char stack[0x300];memset(stack,0x45,sizeof(stack));
    *(uintptr_t*)(stack+0xa8)=game_base+0x10be6c5;
    CONTEXT expected={0},actual={0};expected.Rsp=(DWORD64)stack;
    expected.Rip=game_base+0x1099270;actual=expected;actual.Rip=pc;
    DWORD64 native_base=0,relay_base=0,frame;void *handler;
    RUNTIME_FUNCTION *native=RtlLookupFunctionEntry(expected.Rip,&native_base,NULL);
    RUNTIME_FUNCTION *relay=RtlLookupFunctionEntry(actual.Rip,&relay_base,NULL);
    if(!native || !relay || native_base!=game_base || relay_base!=game_base)return FALSE;
    RtlVirtualUnwind(UNW_FLAG_NHANDLER,native_base,expected.Rip,native,&expected,&handler,&frame,NULL);
    RtlVirtualUnwind(UNW_FLAG_NHANDLER,relay_base,actual.Rip,relay,&actual,&handler,&frame,NULL);
    return expected.Rsp==actual.Rsp && expected.Rip==actual.Rip &&
        !memcmp(&expected.Xmm6,&actual.Xmm6,10*sizeof(M128A));
}
int main(void) {
    game_base=(uintptr_t)VirtualAlloc(NULL,0x7155000,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
    if(!game_base)return 1;fill_native_fixture(game_base);
    const DWORD calls[4]={0x10be322,0x10be3ed,0x10be519,0x10be6c0};
    for(unsigned i=0;i<4;i++) {
        unsigned char *call=(unsigned char*)(game_base+calls[i]);call[0]=0xe8;
        int32_t relative=(int32_t)(0x1099200-(calls[i]+5));memcpy(call+1,&relative,4);
    }
    memcpy((void*)(game_base+0x10be1bf),"\x4c\x8b\xf1",3);
    /* A real CALL at the verified type0 site; explicitly forwards stack args
     * and preserves R14 while supplying the caller's primary view register. */
    const unsigned char prefix[]={0x41,0x56,0x48,0x83,0xec,0x30,
        0x48,0x8b,0x44,0x24,0x60,0x48,0x89,0x44,0x24,0x20,
        0x48,0x8b,0x44,0x24,0x68,0x48,0x89,0x44,0x24,0x28,
        0x4c,0x8b,0x74,0x24,0x70};
    for(unsigned i=0;i<4;i++) {
        unsigned char *stub=(unsigned char*)(game_base+calls[i]-0x40);
        memset(stub,0x90,0x40);memcpy(stub,prefix,sizeof(prefix));
        memcpy(stub+0x45,"\x48\x83\xc4\x30\x41\x5e\xc3",7);
    }
    DWORD old;
    if(!VirtualProtect((void*)game_base,0x7155000,PAGE_EXECUTE_READ,&old))return 2;
    if(!VirtualProtect((void*)(game_base+0x6739000),4096,PAGE_READWRITE,&old) ||
       !VirtualProtect((void*)(game_base+0x5339000),4096,PAGE_READWRITE,&old))return 3;
    FlushInstructionCache(GetCurrentProcess(),(void*)game_base,0x7155000);
    if(!RtlAddFunctionTable(light_native_rows,5,game_base))return 4;
    unsigned char light[0x170]={0},view[0x2080]={0},other[0x2080]={0};
    *(void**)(game_base+0x6739b10)=view;
    set_float(light,0x98,-.5f);set_float(light,0x9c,.01f);set_float(light,0xa0,100);
    set_float(light,0xa8,.2f);set_float(light,0xac,.4f);set_float(light,0xb0,.6f);
    set_float(light,0xc8,.7f);set_float(light,0xcc,75);
    InvokeFn invoke=(InvokeFn)(game_base+calls[3]-0x40);LightFn foreign=(LightFn)(game_base+0x1099200);
    unsigned char *site=(unsigned char*)(game_base+0x1099270);
    if(!VirtualProtect(site,8,PAGE_EXECUTE_READWRITE,&old))return 5;
    site[0]=0x90;
    if(prepare_photo_light() || photo_light_patch.page)return 6;
    site[0]=light_native_code[0x70];VirtualProtect(site,8,old,&old);
    if(!prepare_photo_light() || !photo_light_patch.registered)return 7;
    /* RIP points at instructions, not bytes embedded in address immediates.
     * Probe every real relay instruction, including the tail JMP. */
    unsigned tested_instructions=0;
    for(unsigned i=0;i<photo_light_relay_size;) {
        unsigned size=relay_instruction_size(photo_light_patch.page+i);
        if(!size || i+size>photo_light_relay_size || !compare_unwind((uintptr_t)photo_light_patch.page+i)) {
            printf("Unwind failure at real instruction offset=%u\n",i);return 8;
        }
        i+=size;tested_instructions++;
    }
    float expected[5],actual[5];const float fronts[]={0,60,85,100,200},centres[]={25,80,150};
    for(unsigned caller=0;caller<4;caller++)for(unsigned start=0;start<2;start++)for(unsigned debug=0;debug<2;debug++)
    for(unsigned near_flag=0;near_flag<2;near_flag++)for(unsigned spec=0;spec<2;spec++)for(unsigned kind=0;kind<2;kind++)
    for(unsigned f=0;f<5;f++)for(unsigned c=0;c<3;c++) {
        set_float(light,0xa4,start?70:0);*(unsigned char*)(game_base+0x53394ec)=(unsigned char)debug;
        invoke=(InvokeFn)(game_base+calls[caller]-0x40);
        unsigned flags=16|(near_flag<<19)|(spec<<20)|(kind*2);
        geometry_active=0;
        if(!evaluate(invoke,light,flags&~(1u<<20),fronts[f],centres[c],view,expected))return 9;
        geometry_active=1;
        if(!evaluate(invoke,light,flags|(1<<18),fronts[f],centres[c],view,actual))return 10;
        for(unsigned j=0;j<5;j++)if(!same(actual[j],expected[j]))return 11;
        cases++;
    }
    if(photo_light_hits!=1920)return 16;
    set_float(light,0xa4,70);*(unsigned char*)(game_base+0x53394ec)=0;
    *(unsigned*)(light+0x88)=1u<<20;unsigned old_kind=99;
    foreign(light,85,80,expected,expected+3,&old_kind);
    if(!evaluate(invoke,light,(1u<<18)|(1u<<20),85,80,view,actual))return 70;
    if(!same(expected[3],0) || old_kind!=1 || !same(actual[3],.7f) || actual[4]!=0)return 71;
    printf("Ordinary specular example at85: prior RGB-only override specular=%g/type=%u; new specular=%g/type=%g.\n",expected[3],old_kind,actual[3],actual[4]);
    set_float(light,0xa4,70);*(unsigned char*)(game_base+0x53394ec)=0;
    unsigned flags=1<<18;
    /* Ctrl off, unpublished relay, auxiliary view, foreign caller and restored
     * instruction must all retain the original camera-distance fade. */
    for(unsigned mode=0;mode<5;mode++) {
        geometry_active=mode!=0;photo_light_ready=mode!=1;
        void *which=mode==2?other:view;
        if(mode==3) {
            *(unsigned*)(light+0x88)=flags;unsigned kind;foreign(light,85,80,actual,actual+3,&kind);
        } else {
            if(mode==4 && !photo_light_change(FALSE))return 12;
            if(!evaluate(invoke,light,flags,85,80,which,actual))return 13;
        }
        if(!same(actual[0],.1f) || !same(actual[1],.2f) || !same(actual[2],.3f))return 14;
    }
    if(memcmp(site,light_native_code+0x70,8))return 15;
    printf("PhotoLightProbe passed: real native helper/relay, %u arithmetic cases, source immutable, Ctrl/ready/primary/caller gates, all %u relay instruction starts unwind, atomic restore.\n",cases,tested_instructions);
    return 0;
}
