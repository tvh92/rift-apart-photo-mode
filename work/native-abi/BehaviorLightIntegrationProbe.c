#include <windows.h>
#include <stdio.h>
static BOOL test_shift,test_stop;
static SHORT FakeKey(int key) { return ((key==VK_SHIFT && test_shift) || (test_stop && (key==VK_CONTROL || key==VK_MENU || key==VK_F10))) ? (SHORT)0x8000:0; }
static HWND FakeWindow(void) { return (HWND)1; }
static DWORD FakeWindowPid(HWND window,LPDWORD pid) { (void)window;*pid=GetCurrentProcessId();return 1; }
#define GetAsyncKeyState FakeKey
#define GetForegroundWindow FakeWindow
#define GetWindowThreadProcessId FakeWindowPid
#define HID_EXPORT_COUNT 44
#include "../../outputs/camera-native-lighting-candidate/CameraBoost.c"
int main(void) {
 unsigned char camera[0x150]={0},motion[0x100]={0},other[0x100]={0};
 game_base=0x10000000;
 *(uintptr_t*)camera=game_base+0x45fd8b0;
 *(uintptr_t*)(camera+0xd8)=game_base+0x4690b30;
 *(uintptr_t*)(camera+0xf0)=game_base+0x4690a50;
 *(DWORD*)(camera+0x1c)=0x123456;
 *(uintptr_t*)motion=game_base+0x45fdef0;*(DWORD*)(motion+0x1c)=0x123458;*(DWORD*)(motion+0x44)=0x123456;
 *(float*)(motion+0x68)=1000;*(float*)(motion+0x6c)=20;*(float*)(motion+0x70)=10000;*(float*)(motion+0x84)=10;
 memcpy(other,motion,sizeof(motion));*(DWORD*)(other+0x44)=0x654321;
 CaptureFree(camera);UpdateMotion(other);
 if(last_motion || memcmp(other+0x68,motion+0x68,8))return 1;
 UpdateMotion(motion);
 if(*(float*)(motion+0x6c)!=20 || *(float*)(motion+0x84)!=10)return 2;
 test_shift=TRUE;UpdateMotion(motion);
 if(*(float*)(motion+0x6c)!=200 || *(float*)(motion+0x84)!=100 || *(float*)(motion+0x70)!=100000)return 3;
 test_shift=FALSE;UpdateMotion(motion);
 if(*(float*)(motion+0x6c)!=20 || *(float*)(motion+0x84)!=10)return 4;
 enabled=FALSE;*(float*)(motion+0x6c)=200;UpdateMotion(motion);
 if(*(float*)(motion+0x6c)!=20 || *(float*)(motion+0x84)!=10)return 5;
 /* A replacement Free-camera identity gets a new matching controller baseline. */
 enabled=TRUE;*(DWORD*)(camera+0x1c)=0x234567;*(DWORD*)(motion+0x44)=0x234567;*(DWORD*)(motion+0x1c)=0x234568;
 CaptureFree(camera);test_shift=TRUE;UpdateMotion(motion);
 if(*(float*)(motion+0x6c)!=200 || last_motion_id!=0x234568)return 6;
 unsigned char *collision_page=VirtualAlloc(NULL,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);
 const unsigned char collision_original[9]={0xe8,0x44,0xaa,0x75,0xff,0x84,0xc0,0x74,0x3b};
 if(!collision_page)return 7;
 memcpy(collision_page,collision_original,9);
 if(!prepare_collision_bypass(collision_page))return 8;
 unsigned char *geometry_page=VirtualAlloc(NULL,65536,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);
 if(!geometry_page)return 10;
 const unsigned char windows[2][11]={{0x03,0xf8,0x8b,0x84,0x24,0xd8,0,0,0,0x23,0xf8},{0x03,0xf8,0x8b,0x84,0x24,0x80,0,0,0,0x23,0xf8}};
 memcpy(geometry_page,windows[0],11);memcpy(geometry_page+4096,windows[1],11);
 geometry_page[8192]=1;geometry_page[8208]=1;
 RUNTIME_FUNCTION native_frames[2]={{0,16,8192},{4096,4112,8208}};
 if(!geometry_prepare(&geometry_patch,(uintptr_t)geometry_page,(uintptr_t)geometry_page+65536,geometry_page,geometry_page+4096,&geometry_active,native_frames) || !geometry_install(&geometry_patch))return 11;
 geometry_ready=TRUE;InterlockedExchange(&geometry_active,1);
 test_stop=TRUE;UpdateMotion(motion);
 if(enabled || collision_changed || memcmp(collision_page,collision_original,9) || *(float*)(motion+0x6c)!=20)return 9;
 if(geometry_active || memcmp(geometry_page,windows[0],11) || memcmp(geometry_page+4096,windows[1],11))return 12;
 VirtualFree(collision_page,0,MEM_RELEASE);
 puts("PASS: owner filtering, normal/Shift/release speeds, baseline restore, replacement camera identity, and hotkey restoration of collision plus both geometry selectors.");return 0;
}
