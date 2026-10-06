/* A fading, click-through status card owned by this process. Runs on its own
 * message thread; never calls graphics APIs or changes the game's input focus. */
#ifndef PHOTO_STATUS_INDICATOR_H
#define PHOTO_STATUS_INDICATOR_H
#define PHOTO_STATUS_MESSAGE (WM_APP+0x461)
static volatile LONG indicator_thread_id,indicator_pending_mode=-1,indicator_serial;
static PVOID volatile indicator_pending_target;
static SRWLOCK indicator_request_lock=SRWLOCK_INIT;
typedef struct {
    HWND window,target;
    HDC dc;
    HBITMAP bitmap;
    HGDIOBJ old_bitmap;
    uint32_t *pixels;
    int width,height,dpi;
    ULONGLONG shown_at;
    BOOL showing,on;
} PhotoIndicator;
static PhotoIndicator photo_indicator;

static BYTE indicator_opacity(ULONGLONG elapsed) {
    if(elapsed<900)return 255;
    if(elapsed>=1600)return 0;
    return (BYTE)((1600-elapsed)*255/700);
}
static void indicator_free_bitmap(PhotoIndicator *ui) {
    if(ui->dc && ui->old_bitmap)SelectObject(ui->dc,ui->old_bitmap);
    if(ui->bitmap)DeleteObject(ui->bitmap);
    if(ui->dc)DeleteDC(ui->dc);
    ui->bitmap=NULL;ui->dc=NULL;ui->pixels=NULL;ui->old_bitmap=NULL;
}
static BOOL indicator_bitmap(PhotoIndicator *ui,BOOL on,int dpi) {
    indicator_free_bitmap(ui);
    ui->dpi=dpi;ui->width=MulDiv(280,dpi,96);ui->height=MulDiv(52,dpi,96);
    BITMAPINFO info={0};info.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);
    info.bmiHeader.biWidth=ui->width;info.bmiHeader.biHeight=-ui->height;
    info.bmiHeader.biPlanes=1;info.bmiHeader.biBitCount=32;info.bmiHeader.biCompression=BI_RGB;
    ui->dc=CreateCompatibleDC(NULL);
    if(!ui->dc)return FALSE;
    ui->bitmap=CreateDIBSection(ui->dc,&info,DIB_RGB_COLORS,(void**)&ui->pixels,NULL,0);
    if(!ui->bitmap) {indicator_free_bitmap(ui);return FALSE;}
    ui->old_bitmap=SelectObject(ui->dc,ui->bitmap);
    memset(ui->pixels,0,(size_t)ui->width*ui->height*4);
    HBRUSH background=CreateSolidBrush(RGB(22,27,36));
    HPEN border=CreatePen(PS_SOLID,1,RGB(55,64,77));
    if(!background || !border) {if(background)DeleteObject(background);if(border)DeleteObject(border);indicator_free_bitmap(ui);return FALSE;}
    HGDIOBJ old_brush=SelectObject(ui->dc,background),old_pen=SelectObject(ui->dc,border);
    int corner=MulDiv(18,dpi,96);
    RoundRect(ui->dc,0,0,ui->width,ui->height,corner,corner);
    HBRUSH dot=CreateSolidBrush(on?RGB(105,226,160):RGB(170,181,197));
    if(dot) {
        SelectObject(ui->dc,dot);SelectObject(ui->dc,GetStockObject(NULL_PEN));
        Ellipse(ui->dc,MulDiv(21,dpi,96),MulDiv(21,dpi,96),MulDiv(31,dpi,96),MulDiv(31,dpi,96));
        SelectObject(ui->dc,background);DeleteObject(dot);
    }
    SelectObject(ui->dc,old_pen);SelectObject(ui->dc,old_brush);
    DeleteObject(background);DeleteObject(border);
    HFONT font=CreateFontW(-MulDiv(19,dpi,96),0,0,0,FW_SEMIBOLD,FALSE,FALSE,FALSE,
        DEFAULT_CHARSET,OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,ANTIALIASED_QUALITY,DEFAULT_PITCH,L"Segoe UI");
    if(!font) {indicator_free_bitmap(ui);return FALSE;}
    HGDIOBJ old_font=SelectObject(ui->dc,font);
    SetBkMode(ui->dc,TRANSPARENT);SetTextColor(ui->dc,RGB(241,245,251));
    RECT text={MulDiv(47,dpi,96),0,ui->width-MulDiv(15,dpi,96),ui->height};
    DrawTextW(ui->dc,on?L"Detail override: ON":L"Detail override: OFF",-1,&text,DT_LEFT|DT_VCENTER|DT_SINGLELINE|DT_NOPREFIX);
    SelectObject(ui->dc,old_font);DeleteObject(font);GdiFlush();
    /* GDI supplies RGB but no alpha. Outside the rounded card remains zero;
     * inside, assign a translucent alpha and premultiply RGB for ULW_ALPHA. */
    for(int i=0;i<ui->width*ui->height;i++) {
        uint32_t color=ui->pixels[i]&0xffffff;
        if(color) {
            unsigned r=((color>>16)&255)*232/255,g=((color>>8)&255)*232/255,b=(color&255)*232/255;
            ui->pixels[i]=0xe8000000|(r<<16)|(g<<8)|b;
        }
    }
    return TRUE;
}
static BOOL indicator_target_valid(HWND target) {
    DWORD process=0;
    if(!target || !IsWindow(target) || !IsWindowVisible(target) || IsIconic(target))return FALSE;
    GetWindowThreadProcessId(target,&process);
    if(process!=GetCurrentProcessId())return FALSE;
    GetWindowThreadProcessId(GetForegroundWindow(),&process);
    return process==GetCurrentProcessId();
}
static void indicator_hide(PhotoIndicator *ui) {
    ui->showing=FALSE;
    if(ui->window) {KillTimer(ui->window,1);ShowWindow(ui->window,SW_HIDE);}
}
static BOOL indicator_frame(PhotoIndicator *ui,BYTE alpha) {
    RECT client;POINT origin={0,0};
    if(!GetClientRect(ui->target,&client) || !ClientToScreen(ui->target,&origin))return FALSE;
    if(client.right<ui->width || client.bottom<ui->height)return FALSE;
    POINT destination={origin.x+(client.right-ui->width)/2,origin.y+MulDiv(26,ui->dpi,96)},source={0,0};
    SIZE size={ui->width,ui->height};BLENDFUNCTION blend={AC_SRC_OVER,0,alpha,AC_SRC_ALPHA};
    return UpdateLayeredWindow(ui->window,NULL,&destination,&size,ui->dc,&source,0,&blend,ULW_ALPHA);
}
static void indicator_apply_pending(PhotoIndicator *ui) {
    AcquireSRWLockShared(&indicator_request_lock);
    int mode=indicator_pending_mode;HWND target=(HWND)indicator_pending_target;LONG serial=indicator_serial;
    ReleaseSRWLockShared(&indicator_request_lock);
    if(mode<0 || !indicator_target_valid(target)) {indicator_hide(ui);return;}
    typedef UINT (WINAPI *DpiFn)(HWND);
    FARPROC dpi_address=GetProcAddress(GetModuleHandleW(L"user32.dll"),"GetDpiForWindow");
    DpiFn dpi_function=NULL;memcpy(&dpi_function,&dpi_address,sizeof(dpi_function));
    int dpi=dpi_function?(int)dpi_function(target):96;if(dpi<96 || dpi>384)dpi=96;
    ui->target=target;ui->on=mode==1;
    if(!indicator_bitmap(ui,ui->on,dpi) || !indicator_frame(ui,255)) {
        indicator_hide(ui);log_line("Photo status indicator could not render; detail toggle remains available.");return;
    }
    if(InterlockedCompareExchange(&indicator_serial,0,0)!=serial)return;
    SetWindowLongPtrW(ui->window,GWLP_HWNDPARENT,(LONG_PTR)target);
    SetWindowPos(ui->window,HWND_TOPMOST,0,0,0,0,SWP_NOMOVE|SWP_NOSIZE|SWP_NOACTIVATE);
    ui->shown_at=GetTickCount64();ui->showing=TRUE;
    ShowWindow(ui->window,SW_SHOWNOACTIVATE);SetTimer(ui->window,1,33,NULL);
}
static LRESULT CALLBACK indicator_window_proc(HWND window,UINT message,WPARAM wparam,LPARAM lparam) {
    PhotoIndicator *ui=&photo_indicator;
    if(message==WM_NCHITTEST)return HTTRANSPARENT;
    if(message==WM_MOUSEACTIVATE)return MA_NOACTIVATE;
    if(message==WM_TIMER && wparam==1) {
        BYTE alpha=indicator_opacity(GetTickCount64()-ui->shown_at);
        if(!alpha || !indicator_target_valid(ui->target) || !indicator_frame(ui,alpha))indicator_hide(ui);
        return 0;
    }
    if(message==WM_DESTROY) {indicator_hide(ui);indicator_free_bitmap(ui);PostQuitMessage(0);return 0;}
    return DefWindowProcW(window,message,wparam,lparam);
}
static DWORD WINAPI indicator_worker(LPVOID unused) {
    (void)unused;
    const wchar_t *name=L"RiftApartPhotoDetailStatus";
    WNDCLASSW klass={0};klass.lpfnWndProc=indicator_window_proc;klass.hInstance=own_module;klass.lpszClassName=name;
    if(!RegisterClassW(&klass) && GetLastError()!=ERROR_CLASS_ALREADY_EXISTS) {
        log_line("Photo status indicator could not register its window.");return 0;
    }
    photo_indicator.window=CreateWindowExW(WS_EX_LAYERED|WS_EX_TRANSPARENT|WS_EX_NOACTIVATE|WS_EX_TOOLWINDOW,
        name,L"Photo Mode detail status",WS_POPUP,0,0,0,0,NULL,NULL,own_module,NULL);
    if(!photo_indicator.window) {log_line("Photo status indicator could not create its window.");return 0;}
    MSG message;PeekMessageW(&message,NULL,0,0,PM_NOREMOVE);
    InterlockedExchange(&indicator_thread_id,(LONG)GetCurrentThreadId());
    if(InterlockedCompareExchange(&indicator_serial,0,0)>0)indicator_apply_pending(&photo_indicator);
    while(GetMessageW(&message,NULL,0,0)>0) {
        if(!message.hwnd && message.message==PHOTO_STATUS_MESSAGE)indicator_apply_pending(&photo_indicator);
        else {TranslateMessage(&message);DispatchMessageW(&message);}
    }
    DestroyWindow(photo_indicator.window);photo_indicator.window=NULL;
    InterlockedExchange(&indicator_thread_id,0);return 0;
}
static void StartPhotoIndicator(void) {
    HANDLE thread=CreateThread(NULL,0,indicator_worker,NULL,0,NULL);
    if(thread)CloseHandle(thread);else log_line("Photo status indicator thread unavailable.");
}
static void ShowPhotoIndicator(BOOL on,HWND target) {
    AcquireSRWLockExclusive(&indicator_request_lock);
    InterlockedExchangePointer(&indicator_pending_target,target);
    InterlockedExchange(&indicator_pending_mode,on?1:0);
    InterlockedIncrement(&indicator_serial);
    ReleaseSRWLockExclusive(&indicator_request_lock);
    LONG thread=InterlockedCompareExchange(&indicator_thread_id,0,0);
    if(thread)PostThreadMessageW((DWORD)thread,PHOTO_STATUS_MESSAGE,0,0);
}
static void HidePhotoIndicator(void) {
    AcquireSRWLockExclusive(&indicator_request_lock);
    if(InterlockedExchange(&indicator_pending_mode,-1)<0) {ReleaseSRWLockExclusive(&indicator_request_lock);return;}
    InterlockedIncrement(&indicator_serial);
    ReleaseSRWLockExclusive(&indicator_request_lock);
    LONG thread=InterlockedCompareExchange(&indicator_thread_id,0,0);
    if(thread)PostThreadMessageW((DWORD)thread,PHOTO_STATUS_MESSAGE,0,0);
}
#endif
