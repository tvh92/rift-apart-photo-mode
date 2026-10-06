/* Isolated real relay/ABI/cache/restore exercise. Never opens the game. */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include "../../outputs/camera-native-status-candidate/GeometryLOD.h"
static uintptr_t game_base;
static volatile LONG geometry_active;
#include "../../outputs/camera-native-status-candidate/PhotoFog.h"
static unsigned calls;
static void *expected_job,*expected_lighting;
static unsigned char observed[0x84];
static void FakeFog(void *job,void *lighting) {
    if(job!=expected_job || lighting!=expected_lighting)ExitProcess(90);
    memcpy(observed,*(unsigned char**)((unsigned char*)job+0x578)+0x110,sizeof(observed));calls++;
}
static void pattern(unsigned char *p,unsigned char byte) {memset(p+0x110,byte,0x84);}
static int matching(unsigned char byte) {
    for(unsigned i=0;i<sizeof(observed);i++)if(observed[i]!=byte)return 0;
    return 1;
}
int main(void) {
    game_base=(uintptr_t)VirtualAlloc(NULL,0x7155000,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
    if(!game_base)return 1;
    unsigned char job[0x870]={0},block[0x760]={0},view[0x2080]={0},clone[0x2080]={0},other[0x2080]={0};
    *(void**)(job+0x570)=clone;*(void**)(job+0x578)=block;
    *(void**)(game_base+0x6739b10)=view;
    expected_job=job;expected_lighting=(void*)0x1234;
    unsigned char *site=(unsigned char*)(game_base+0x12bd0b0);
    const unsigned char native[8]={0xe8,0xeb,0x95,0xcf,0xff,0x4d,0x85,0xf6};
    const unsigned char prefix[8]={0x57,0x48,0x83,0xec,0x20,0x4c,0x89,0xc7};
    const unsigned char suffix[6]={0x48,0x83,0xc4,0x20,0x5f,0xc3};
    memcpy(site-8,prefix,8);memcpy(site,native,8);memcpy(site+8,suffix,6);
    memcpy((void*)(game_base+0x12bce27),"\x48\x8b\xf9",3);
    unsigned char *fake=(unsigned char*)(game_base+0xfb66a0);
    fake[0]=0x48;fake[1]=0xb8;uintptr_t target=(uintptr_t)FakeFog;
    memcpy(fake+2,&target,8);fake[10]=0xff;fake[11]=0xe0;
    DWORD old;
    if(!VirtualProtect((void*)game_base,0x7155000,PAGE_EXECUTE_READ,&old))return 2;
    /* Its data global remains writable, as it is in the actual executable. */
    if(!VirtualProtect((void*)(game_base+0x6739000),4096,PAGE_READWRITE,&old))return 3;
    FlushInstructionCache(GetCurrentProcess(),(void*)game_base,0x7155000);
    void (*invoke)(void*,void*,void*)=(void(*)(void*,void*,void*))(site-8);
    pattern(block,0x11);invoke(job,expected_lighting,view);
    if(!matching(0x11) || calls!=1)return 4;
    /* Exact-window refusal must not publish a relay or mutate the callsite. */
    if(!VirtualProtect(site,8,PAGE_EXECUTE_READWRITE,&old))return 5;
    site[0]=0x90;
    if(prepare_photo_fog() || photo_fog_patch.page)return 6;
    site[0]=native[0];VirtualProtect(site,8,old,&old);
    if(!prepare_photo_fog() || !photo_fog_patch.sites[0].changed)return 7;
    if(memcmp(site+5,native+5,3) || memcmp(site-8,prefix,8) || memcmp(site+8,suffix,6))return 8;
    /* Non-Photo frames stay native. */
    pattern(block,0x22);invoke(job,expected_lighting,view);
    if(!matching(0x22) || photo_fog_cached)return 9;
    /* A prepared/reachable relay with an unpublished install stays transparent. */
    photo_fog_ready=0;photo_fog_session_update(TRUE);geometry_active=1;
    pattern(block,0x2b);invoke(job,expected_lighting,view);
    if(!matching(0x2b) || photo_fog_cached)return 19;
    photo_fog_session_update(FALSE);photo_fog_ready=1;
    /* Cache even when preference starts off; turning it on later uses entry. */
    photo_fog_session_update(TRUE);geometry_active=0;
    pattern(block,0x33);invoke(job,expected_lighting,view);
    if(!matching(0x33) || !photo_fog_cached)return 10;
    geometry_active=1;pattern(block,0x44);memset(block+0x194,0xa5,8);
    invoke(job,expected_lighting,view);
    if(!matching(0x33) || block[0x194]!=0xa5 || block[0x19b]!=0xa5)return 11;
    /* Auxiliary view, mismatched clone index, and disabled preference excluded. */
    pattern(block,0x55);invoke(job,expected_lighting,other);if(!matching(0x55))return 12;
    *(int*)(clone+0xf90)=1;invoke(job,expected_lighting,view);if(!matching(0x55))return 13;
    *(int*)(clone+0xf90)=0;geometry_active=0;
    pattern(block,0x66);invoke(job,expected_lighting,view);if(!matching(0x66))return 14;
    geometry_active=1;photo_fog_session_update(FALSE);
    pattern(block,0x77);invoke(job,expected_lighting,view);
    if(!matching(0x77) || photo_fog_cached)return 15;
    photo_fog_session_update(TRUE);pattern(block,0x88);invoke(job,expected_lighting,view);
    pattern(block,0x99);invoke(job,expected_lighting,view);if(!matching(0x88))return 16;
    if(!photo_fog_change(FALSE) || memcmp(site,native,8))return 17;
    pattern(block,0xaa);invoke(job,expected_lighting,view);if(!matching(0xaa))return 18;
    printf("PhotoFogProbe passed: real relay ABI, exact guards, entry cache, toggle, auxiliary views, exit/reentry, untouched texture tail, callsite restoration; calls=%u\n",calls);
    return 0;
}
