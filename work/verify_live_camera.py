import ctypes as C, struct, json
from ctypes import wintypes as W
k=C.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
k.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];k.ReadProcessMemory.restype=W.BOOL
k.CloseHandle.argtypes=[W.HANDLE]
s=json.load(open('outputs/camera-controls/boost-status.json'))
h=k.OpenProcess(0x1010,False,s['pid'])
if not h:raise C.WinError(C.get_last_error())
def read(a,n):
 b=C.create_string_buffer(n);g=C.c_size_t()
 if not k.ReadProcessMemory(h,C.c_void_p(a),b,n,C.byref(g)) or g.value!=n:raise C.WinError(C.get_last_error())
 return b.raw
try:
 o=int(s['object'],16);m=int(s['motion_object'],16)
 print(json.dumps({'state':s['state'],'free_values':struct.unpack('<4f',read(o+0xf8,16)),'movement_values':{name:struct.unpack('<f',read(m+off,4))[0] for name,off in {'tether':0x68,'move':0x6c,'acceleration':0x70,'rise':0x84}.items()}}))
finally:k.CloseHandle(h)
