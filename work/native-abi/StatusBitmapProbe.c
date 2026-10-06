#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static HMODULE own_module;
static void log_line(const char *text) {(void)text;}
#include "../../outputs/camera-native-status-candidate/PhotoIndicator.h"
int main(void) {
    PhotoIndicator ui={0};own_module=GetModuleHandleW(NULL);
    if(indicator_opacity(0)!=255 || indicator_opacity(899)!=255 || indicator_opacity(900)!=255 ||
       indicator_opacity(1250)!=127 || indicator_opacity(1599)>1 || indicator_opacity(1600)!=0)return 1;
    unsigned previous=255;for(int i=0;i<2000;i++) {unsigned a=indicator_opacity(i);if(a>previous)return 2;previous=a;}
    /* Warm up stock GDI objects before measuring owned-object cleanup. */
    if(!indicator_bitmap(&ui,TRUE,96))return 17;
    indicator_free_bitmap(&ui);
    DWORD before=GetGuiResources(GetCurrentProcess(),GR_GDIOBJECTS);
    for(int dpi=96;dpi<=192;dpi+=48)for(int on=0;on<2;on++) {
        if(!indicator_bitmap(&ui,on,dpi))return 3;
        if(ui.width!=MulDiv(280,dpi,96) || ui.height!=MulDiv(52,dpi,96) || ui.pixels[0])return 4;
        int visible=0,bright=0;
        for(int i=0;i<ui.width*ui.height;i++) {
            uint32_t color=ui.pixels[i];unsigned a=color>>24;
            if((color&255)>a || ((color>>8)&255)>a || ((color>>16)&255)>a)return 5;
            if(a)visible++;if((color&255)>170)bright++;
        }
        if(visible<ui.width*ui.height/2 || bright<100)return 6;
        if(dpi==96) {
            char name[160];snprintf(name,sizeof(name),"work/native-abi/status-%s.bgra",on?"on":"off");
            FILE *f=fopen(name,"wb");if(!f)return 7;
            fwrite(ui.pixels,4,(size_t)ui.width*ui.height,f);fclose(f);
        }
    }
    indicator_free_bitmap(&ui);
    DWORD after=GetGuiResources(GetCurrentProcess(),GR_GDIOBJECTS);
    if(after>before) {printf("GDI before=%lu after=%lu\n",before,after);return 8;}
    /* Create its actual native window, hidden: inspect input styles/hit tests
     * without showing a test popup on the user's desktop. */
    WNDCLASSW c={0};c.lpfnWndProc=indicator_window_proc;c.hInstance=own_module;c.lpszClassName=L"PhotoIndicatorProbe";
    if(!RegisterClassW(&c))return 9;
    HWND w=CreateWindowExW(WS_EX_LAYERED|WS_EX_TRANSPARENT|WS_EX_NOACTIVATE|WS_EX_TOOLWINDOW,
        c.lpszClassName,L"",WS_POPUP,0,0,280,52,NULL,NULL,own_module,NULL);
    if(!w)return 10;
    LONG_PTR styles=GetWindowLongPtrW(w,GWL_EXSTYLE);
    LONG_PTR needed=WS_EX_LAYERED|WS_EX_TRANSPARENT|WS_EX_NOACTIVATE|WS_EX_TOOLWINDOW;
    if((styles&needed)!=needed || SendMessageW(w,WM_NCHITTEST,0,0)!=HTTRANSPARENT ||
       SendMessageW(w,WM_MOUSEACTIVATE,0,0)!=MA_NOACTIVATE || IsWindowVisible(w))return 11;
    if(!indicator_bitmap(&ui,TRUE,96))return 12;
    POINT destination={0,0},source={0,0};SIZE size={ui.width,ui.height};BLENDFUNCTION blend={AC_SRC_OVER,0,255,AC_SRC_ALPHA};
    if(!UpdateLayeredWindow(w,NULL,&destination,&size,ui.dc,&source,0,&blend,ULW_ALPHA))return 13;
    indicator_free_bitmap(&ui);DestroyWindow(w);
    ShowPhotoIndicator(TRUE,NULL);if(indicator_pending_mode!=1)return 14;
    ShowPhotoIndicator(FALSE,NULL);if(indicator_pending_mode!=0)return 15;
    HidePhotoIndicator();LONG serial=indicator_serial;HidePhotoIndicator();
    if(indicator_pending_mode!=-1 || indicator_serial!=serial)return 16;
    puts("PASS: native ON/OFF bitmap at 96/144/192 DPI, premultiplied transparency, monotonic timed fade, GDI resource cleanup, click-through/no-activation styles, hidden layered-window render, coalesced hide requests.");
    return 0;
}
