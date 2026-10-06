"""Exercise the actual two-byte-patched DLL with API fakes in this Python process.
Never opens or writes the game process. Original import slots/globals are restored.
"""
import ctypes as C, hashlib, os, struct
from pathlib import Path

p=Path('outputs/camera-native/hid.dll').resolve()
assert hashlib.sha256(p.read_bytes()).hexdigest()=='5c36943c6dfb45713382bf471e6f9939f857ee94f7789b8fefb2fc3abc292842'
dll=C.WinDLL(str(p));base=dll._handle
k=C.WinDLL('kernel32',use_last_error=True)
k.VirtualProtect.argtypes=[C.c_void_p,C.c_size_t,C.c_ulong,C.POINTER(C.c_ulong)];k.VirtualProtect.restype=C.c_int
pressed=False;focused=True;calls=[]
@C.WINFUNCTYPE(C.c_short,C.c_int)
def key(v):
    calls.append(v);return -32768 if pressed and v==0x11 else 0
@C.WINFUNCTYPE(C.c_void_p)
def foreground():return 1
@C.WINFUNCTYPE(C.c_ulong,C.c_void_p,C.POINTER(C.c_ulong))
def pid(window,result):
    result[0]=os.getpid() if focused else 0;return 1
@C.WINFUNCTYPE(None,C.c_void_p)
def native_tick(obj):pass

def set_slot(rva,pointer):
    address=base+rva;protection=C.c_ulong()
    assert k.VirtualProtect(address,8,4,C.byref(protection)),C.get_last_error()
    old=C.c_void_p.from_address(address).value
    C.c_void_p.from_address(address).value=pointer
    restored=C.c_ulong();assert k.VirtualProtect(address,8,protection.value,C.byref(restored))
    return old

saved=[]
def slot(rva,value):saved.append((rva,set_slot(rva,value)))
geometry_enabled=C.c_int.from_address(base+0x2F024)
enabled=C.c_int.from_address(base+0x2F008)
ready=C.c_int.from_address(base+0x2F224)
down=C.c_int.from_address(base+0x2F65C)
original=[x.value for x in (geometry_enabled,enabled,ready,down)]
photo=C.create_string_buffer(0xC78)
struct.pack_into('<Q',photo,0,0x10000000+0x2FBF630)
struct.pack_into('<I',photo,0x50,4);photo[0x54]=b'\x01'
tick=C.WINFUNCTYPE(None,C.c_void_p)(base+0x2FD0)
try:
    slot(0x2AE40,C.cast(key,C.c_void_p).value)
    slot(0x2AE48,C.cast(foreground,C.c_void_p).value)
    slot(0x2AE50,C.cast(pid,C.c_void_p).value)
    slot(0x2F648,C.cast(native_tick,C.c_void_p).value)
    slot(0x2F1E0,0x10000000)
    geometry_enabled.value=enabled.value=ready.value=1;down.value=0
    tick(photo);assert geometry_enabled.value==1 and calls==[0x11]
    calls.clear();pressed=True;tick(photo)
    assert geometry_enabled.value==0 and calls==[0x11]*3
    tick(photo);assert geometry_enabled.value==0 # no held repeats
    pressed=False;tick(photo);pressed=True;tick(photo);assert geometry_enabled.value==1
    pressed=False;tick(photo);focused=False;pressed=True;tick(photo)
    assert geometry_enabled.value==1 # focus gate preserved
    focused=True;pressed=False;tick(photo);struct.pack_into('<I',photo,0x50,11)
    pressed=True;tick(photo);assert geometry_enabled.value==1 # startup state gate
    print('PASS: actual patched DLL Ctrl rising edge/held suppression, exact key probes, focus/startup gates, original callback and unchanged hook frame.')
finally:
    for rva,value in reversed(saved):set_slot(rva,value)
    for field,value in zip((geometry_enabled,enabled,ready,down),original):field.value=value
