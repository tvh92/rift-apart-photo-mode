/* Real native type4 helper and callsite relay; no game process opened. */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <math.h>
#include "../../outputs/camera-native-lighting-v2/GeometryLOD.h"
static uintptr_t game_base;
static volatile LONG geometry_active,photo_light_hits;
#include "../../outputs/camera-native-lighting-v2/PhotoSpecular.h"
#include "PhotoType4Fixture.h"
typedef float (*Type4Fn)(const void*,const void*);
static void set_float(unsigned char *p,unsigned off,float value){memcpy(p+off,&value,4);}
static BOOL same(float a,float b){return fabsf(a-b)<.000002f;}
int main(void) {
    game_base=(uintptr_t)VirtualAlloc(NULL,0x7155000,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
    if(!game_base)return 1;fill_type4_fixture(game_base);
    if(!RtlAddFunctionTable(spec_native_rows,4,game_base))return 2;
    unsigned char light[0x170]={0},view[0x2080]={0},other[0x2080]={0},before[0x170];
    *(void**)(game_base+0x6739b10)=view;
    set_float(light,0,1);set_float(light,0x14,1);set_float(light,0x28,1);set_float(light,0x4c,1);
    set_float(light,0x98,-.5f);set_float(light,0x9c,.01f);set_float(light,0xa0,100);
    unsigned char *site=(unsigned char*)(game_base+0x10be260),*stub=site-0x1f;
    memset(stub,0x90,0x1f);
    memcpy(stub,"\x41\x56\x48\x83\xec\x20\x4c\x8b\xf2",9);
    memcpy(site-4,"\xb8\x00\x00\x00\x78",5);
    memcpy(site,"\x78\xe8\x2a\xad\xfd\xff\xf3\x0f",8);
    memcpy(site+6,"\xf3\x0f\x11\x44\x24\x18\x48\x83\xc4\x20\x41\x5e\xc3",13);
    DWORD old;
    if(!VirtualProtect((void*)game_base,0x7155000,PAGE_EXECUTE_READ,&old))return 3;
    if(!VirtualProtect((void*)(game_base+0x6739000),4096,PAGE_READWRITE,&old))return 4;
    FlushInstructionCache(GetCurrentProcess(),(void*)game_base,0x7155000);
    Type4Fn native=(Type4Fn)(game_base+0x1098f90),invoke=(Type4Fn)stub;
    if(!VirtualProtect(site,8,PAGE_EXECUTE_READWRITE,&old))return 5;
    site[1]=0x90;
    if(prepare_photo_specular() || photo_specular_patch.page)return 6;
    site[1]=0xe8;VirtualProtect(site,8,old,&old);
    unsigned char *prolog=(unsigned char*)(game_base+0x1098f90);
    if(!VirtualProtect(prolog,1,PAGE_EXECUTE_READWRITE,&old))return 16;
    prolog[0]=0x90;
    if(prepare_photo_specular() || photo_specular_patch.page)return 17;
    prolog[0]=0x40;VirtualProtect(prolog,1,old,&old);
    if(!prepare_photo_specular()) {
        printf("Type4 guard window:");for(unsigned i=0;i<8;i++)printf(" %02x",site[i]);
        printf(" prolog:");for(unsigned i=0;i<12;i++)printf(" %02x",((unsigned char*)(game_base+0x1098f90))[i]);puts("");return 7;
    }
    if(site[0]!=0x78 || site[6]!=0xf3 || site[7]!=0x0f)return 8;
    const float distances[]={0,25,60,85,100,200};unsigned cases=0;
    for(unsigned start=0;start<2;start++)for(unsigned near_flag=0;near_flag<2;near_flag++)
    for(unsigned i=0;i<6;i++) {
        set_float(light,0xa4,start?70:0);set_float(light,0x30,distances[i]);
        *(uint32_t*)(light+0x88)=near_flag<<19;
        float expected=native(light,view);
        *(uint32_t*)(light+0x88)|=1u<<18;memcpy(before,light,sizeof(before));
        geometry_active=1;
        float actual=invoke(light,view);
        if(!same(actual,expected) || memcmp(light,before,sizeof(before)))return 9;
        float faded=native(light,view);
        geometry_active=0;if(!same(invoke(light,view),faded))return 10;
        geometry_active=1;if(!same(invoke(light,other),native(light,other)))return 11;
        photo_specular_ready=0;if(!same(invoke(light,view),faded))return 12;photo_specular_ready=1;
        cases++;
    }
    if(photo_light_hits!=24)return 13;
    set_float(light,0xa4,70);set_float(light,0x30,85);*(uint32_t*)(light+0x88)=1u<<18;
    geometry_active=1;float faded=native(light,view),retained=invoke(light,view);
    if(!same(faded,.5f) || !same(retained,1))return 18;
    printf("Type4 specular example at85: native=%g; retained=%g.\n",faded,retained);
    if(!photo_specular_change(FALSE) || memcmp(site,"\x78\xe8\x2a\xad\xfd\xff\xf3\x0f",8))return 14;
    if(!same(invoke(light,view),native(light,view)))return 15;
    printf("PhotoType4Probe passed: %u native fade cases, near fade/source preservation, exact call/prolog guards, ready/Ctrl/auxiliary gates, adjacent-byte preservation, atomic restore.\n",cases);
    return 0;
}
