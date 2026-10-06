#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static HMODULE own_module;
static HWND simulated_game;
static volatile LONG shown_count,hidden_count;
static void log_line(const char *text) {puts(text);}
static HWND FakeIndicatorFocus(void) {return simulated_game;}
static BOOL FakeIndicatorVisible(HWND window) {return window==simulated_game || IsWindowVisible(window);}
static BOOL FakeIndicatorShow(HWND window,int mode) {
    if(mode==SW_HIDE)InterlockedIncrement(&hidden_count);else InterlockedIncrement(&shown_count);
    /* Exercise the full UI thread without displaying test windows. */
    return ShowWindow(window,SW_HIDE);
}
#define GetForegroundWindow FakeIndicatorFocus
#define IsWindowVisible FakeIndicatorVisible
#define ShowWindow FakeIndicatorShow
#include "../../outputs/camera-native-lighting-v2/PhotoIndicator.h"
static BOOL wait_count(volatile LONG *counter,LONG minimum) {
    for(int i=0;i<150;i++) {
        MSG m;while(PeekMessageW(&m,NULL,0,0,PM_REMOVE)) {TranslateMessage(&m);DispatchMessageW(&m);}
        if(InterlockedCompareExchange(counter,0,0)>=minimum)return TRUE;Sleep(20);
    }
    return FALSE;
}
int main(void) {
    own_module=GetModuleHandleW(NULL);
    simulated_game=CreateWindowExW(0,L"STATIC",L"",WS_POPUP,30,30,1280,720,NULL,NULL,own_module,NULL);
    if(!simulated_game)return 1;
    /* Queue a notice before the worker is ready, then replace it while fading. */
    ShowPhotoIndicator(TRUE,simulated_game);
    if(indicator_started || indicator_thread_id || shown_count)return 11;
    StartPhotoIndicator(NULL);if(indicator_started)return 12;
    StartPhotoIndicator(simulated_game);StartPhotoIndicator(simulated_game);
    if(!wait_count(&shown_count,1))return 2;
    ShowPhotoIndicator(FALSE,simulated_game);
    if(!wait_count(&shown_count,2))return 3;
    if(GetForegroundWindow()!=simulated_game)return 4;
    if(!wait_count(&hidden_count,1))return 5; /* fade timer hides after 1.6 s */
    LONG old_shown=shown_count;ShowPhotoIndicator(TRUE,simulated_game);
    if(!wait_count(&shown_count,old_shown+1))return 6;
    LONG old_hidden=hidden_count;HidePhotoIndicator();
    if(!wait_count(&hidden_count,old_hidden+1))return 7;
    old_shown=shown_count;ShowPhotoIndicator(TRUE,NULL);Sleep(100);
    if(shown_count!=old_shown)return 8; /* invalid/non-game target cannot appear */
    DWORD ui_thread=(DWORD)InterlockedCompareExchange(&indicator_thread_id,0,0);
    if(!ui_thread || !PostThreadMessageW(ui_thread,WM_QUIT,0,0))return 9;
    for(int i=0;i<100 && indicator_thread_id;i++) {
        MSG m;while(PeekMessageW(&m,NULL,0,0,PM_REMOVE)) {TranslateMessage(&m);DispatchMessageW(&m);}Sleep(20);
    }
    if(indicator_thread_id || indicator_started)return 10;
    /* A destroyed owner/quit may be followed by a new valid game window. */
    old_shown=shown_count;ShowPhotoIndicator(FALSE,simulated_game);StartPhotoIndicator(simulated_game);
    if(!wait_count(&shown_count,old_shown+1))return 13;
    ui_thread=(DWORD)indicator_thread_id;PostThreadMessageW(ui_thread,WM_QUIT,0,0);
    for(int i=0;i<100 && indicator_started;i++) {
        MSG m;while(PeekMessageW(&m,NULL,0,0,PM_REMOVE)) {TranslateMessage(&m);DispatchMessageW(&m);}Sleep(20);
    }
    if(indicator_started || indicator_thread_id)return 14;
    DestroyWindow(simulated_game);
    puts("PASS: notifications stay dormant until validated lazy start; duplicate starts rejected; ON/OFF refresh, timer fade, hide, teardown and restart; test windows remained hidden.");
    return 0;
}
