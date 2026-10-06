"""External native Photo Mode speed helper. No DLL, hooks or remote code execution."""
import ctypes as C
from ctypes import wintypes as W
from pathlib import Path
import struct, hashlib, time, json, argparse, sys

GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\RiftApart.exe')
EXE_SHA256 = '51299faca61866cf10ea9035a15b8f22600a56557dd5ffc1aad390d5a54e6d82'
# Exact offsets from the installed EXE's RTTI and the independently inspected
# live object. Refuse other executable builds; never guess these on an update.
FREE_VTABLE = 0x45fd8b0
DATA_VTABLE = 0x4690a50
PRIUS_VTABLE = 0x4690b30
MOTION_VTABLE = 0x45fdef0
DATA_OFFSET = 0xf0
PRIUS_OFFSET = 0xd8
MOTION_FIELDS = {'tether':0x68,'move':0x6c,'acceleration':0x70,'rise':0x84}
OUT = Path(__file__).resolve().parent

class MBI(C.Structure):
    _fields_=[('BaseAddress',C.c_void_p),('AllocationBase',C.c_void_p),('AllocationProtect',W.DWORD),
              ('PartitionId',W.WORD),('RegionSize',C.c_size_t),('State',W.DWORD),('Protect',W.DWORD),('Type',W.DWORD)]
class MODULE(C.Structure):
    _fields_=[('dwSize',W.DWORD),('th32ModuleID',W.DWORD),('th32ProcessID',W.DWORD),('GlblcntUsage',W.DWORD),
              ('ProccntUsage',W.DWORD),('modBaseAddr',C.c_void_p),('modBaseSize',W.DWORD),('hModule',W.HMODULE),
              ('szModule',W.WCHAR*256),('szExePath',W.WCHAR*260)]

def setup():
    k=C.WinDLL('kernel32',use_last_error=True);u=C.WinDLL('user32',use_last_error=True)
    k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
    k.CloseHandle.argtypes=[W.HANDLE]
    k.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];k.ReadProcessMemory.restype=W.BOOL
    k.WriteProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];k.WriteProcessMemory.restype=W.BOOL
    k.VirtualQueryEx.argtypes=[W.HANDLE,C.c_void_p,C.POINTER(MBI),C.c_size_t];k.VirtualQueryEx.restype=C.c_size_t
    k.QueryFullProcessImageNameW.argtypes=[W.HANDLE,W.DWORD,W.LPWSTR,C.POINTER(W.DWORD)];k.QueryFullProcessImageNameW.restype=W.BOOL
    k.CreateToolhelp32Snapshot.argtypes=[W.DWORD,W.DWORD];k.CreateToolhelp32Snapshot.restype=W.HANDLE
    k.Module32FirstW.argtypes=[W.HANDLE,C.POINTER(MODULE)];k.Module32FirstW.restype=W.BOOL
    k.GetExitCodeProcess.argtypes=[W.HANDLE,C.POINTER(W.DWORD)];k.GetExitCodeProcess.restype=W.BOOL
    u.GetAsyncKeyState.argtypes=[C.c_int];u.GetAsyncKeyState.restype=C.c_short
    u.GetForegroundWindow.restype=W.HWND
    u.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)];u.GetWindowThreadProcessId.restype=W.DWORD
    return k,u

def main():
    p=argparse.ArgumentParser();p.add_argument('pid',type=int);p.add_argument('--address',type=lambda s:int(s,0))
    p.add_argument('--normal',type=float,default=10);p.add_argument('--boost',type=float,default=100)
    p.add_argument('--mover-address',type=lambda s:int(s,0))
    p.add_argument('--minutes',type=float,default=120);p.add_argument('--inspect-only',action='store_true');args=p.parse_args()
    assert 0<args.normal<=1000 and 0<args.boost<=1000 and 0<args.minutes<=240
    assert hashlib.sha256(GAME.read_bytes()).hexdigest()==EXE_SHA256,'Unsupported game build; helper disabled.'
    k,u=setup();h=k.OpenProcess(0x1010 if args.inspect_only else 0x1038,False,args.pid)
    if not h:raise C.WinError(C.get_last_error())
    previous=None;obj=None;expected=None;base=None;restored=False;state='starting';mover=None;mover_previous={};mover_expected={}
    def read(address,size):
        buf=C.create_string_buffer(size);got=C.c_size_t()
        if not k.ReadProcessMemory(h,C.c_void_p(address),buf,size,C.byref(got)) or got.value!=size:raise RuntimeError('Camera memory is no longer readable.')
        return buf.raw
    def write(address,data):
        buf=C.create_string_buffer(data);got=C.c_size_t()
        if not k.WriteProcessMemory(h,C.c_void_p(address),buf,len(data),C.byref(got)) or got.value!=len(data):raise RuntimeError('Camera write failed.')
        if read(address,len(data))!=data:raise RuntimeError('Camera write verification failed.')
    def valid(address):
        try:
            return (read(address,8)==struct.pack('<Q',base+FREE_VTABLE) and
                    read(address+PRIUS_OFFSET,8)==struct.pack('<Q',base+PRIUS_VTABLE) and
                    read(address+DATA_OFFSET,8)==struct.pack('<Q',base+DATA_VTABLE))
        except RuntimeError:return False
    def valid_mover(address,camera=None):
        try:
            return (read(address,8)==struct.pack('<Q',base+MOTION_VTABLE) and
                    read(address+0x44,4)==read((obj if camera is None else camera)+0x1c,4))
        except RuntimeError:return False
    def validated_snapshot(camera,motion):
        camera_bytes=read(camera+DATA_OFFSET+8,16)
        motion_bytes={name:read(motion+off,4) for name,off in MOTION_FIELDS.items()}
        values=struct.unpack('<4f',camera_bytes)
        motion_values={name:struct.unpack('<f',data)[0] for name,data in motion_bytes.items()}
        if not (0<values[0]<=10000 and 0<values[1]<=2000 and 0<values[2]<=1000 and 0<values[3]<=1000000):raise RuntimeError('Unexpected camera values; no writes performed.')
        if not (0<motion_values['tether']<=10000 and 0<motion_values['move']<=2000 and 0<motion_values['rise']<=1000 and 0<motion_values['acceleration']<=1000000):raise RuntimeError('Unexpected movement values; no writes performed.')
        if not valid(camera) or not valid_mover(motion,camera):raise RuntimeError('Camera changed while reading its baseline.')
        return camera_bytes,motion_bytes
    def find_nearby(camera):
        info=MBI()
        if not k.VirtualQueryEx(h,C.c_void_p(camera),C.byref(info),C.sizeof(info)) or info.State!=0x1000 or info.RegionSize>64*1024*1024:return None
        frees=set();motions=set();pos=info.BaseAddress;end=pos+info.RegionSize;tail=b''
        buffer=C.create_string_buffer(2*1024*1024)
        patterns=[(struct.pack('<Q',base+FREE_VTABLE),frees),(struct.pack('<Q',base+MOTION_VTABLE),motions)]
        while pos<end:
            amount=min(len(buffer),end-pos);got=C.c_size_t()
            k.ReadProcessMemory(h,C.c_void_p(pos),buffer,amount,C.byref(got))
            if got.value:
                blob=tail+buffer.raw[:got.value]
                for pattern,targets in patterns:
                    off=blob.find(pattern)
                    while off>=0:
                        targets.add(pos-len(tail)+off);off=blob.find(pattern,off+1)
                tail=blob[-7:]
            else:tail=b''
            pos+=amount
        pairs=[(f,m) for f in frees if valid(f) for m in motions if valid_mover(m,f)]
        return pairs[0] if len(pairs)==1 else None
    def status():
        data={'pid':args.pid,'state':state,'object':hex(obj) if obj else None,'motion_object':hex(mover) if mover else None,'normal_multiplier':args.normal,
              'shift_multiplier':args.boost,'original_values':list(struct.unpack('<4f',previous)) if previous else None,
              'restored':restored,'updated_at':time.time()}
        temp=OUT/'boost-status.tmp';temp.write_text(json.dumps(data,indent=2));temp.replace(OUT/'boost-status.json')
    try:
        path=C.create_unicode_buffer(32768);size=W.DWORD(len(path))
        if not k.QueryFullProcessImageNameW(h,0,path,C.byref(size)) or Path(path.value).resolve()!=GAME.resolve():raise RuntimeError('Unexpected process path.')
        snap=k.CreateToolhelp32Snapshot(0x18,args.pid);module=MODULE();module.dwSize=C.sizeof(module)
        try:
            if not k.Module32FirstW(snap,C.byref(module)) or module.szModule.lower()!='riftapart.exe':raise RuntimeError('Cannot identify game module.')
            base=module.modBaseAddr
        finally:k.CloseHandle(snap)
        candidates=set();mover_candidates=set()
        if args.address:
            if not valid(args.address):raise RuntimeError('Supplied object failed all three native type checks.')
            obj=args.address
        if not args.address or not args.mover_address:
            patterns=[(struct.pack('<Q',base+FREE_VTABLE),'free'),(struct.pack('<Q',base+MOTION_VTABLE),'motion')]
            address=0;t0=time.monotonic()
            buffer=C.create_string_buffer(2*1024*1024)
            while address<0x7FFFFFFF0000:
                info=MBI()
                if not k.VirtualQueryEx(h,C.c_void_p(address),C.byref(info),C.sizeof(info)):break
                start=info.BaseAddress or 0;end=start+info.RegionSize
                if end<=address:break
                address=end
                if info.Type!=0x20000 or info.State!=0x1000 or info.Protect&0x100 or (info.Protect&0xff) not in [4,8,0x40,0x80]:continue
                if info.RegionSize>64*1024*1024:continue
                pos=start;tail=b''
                while pos<end:
                    amount=min(len(buffer),end-pos);got=C.c_size_t()
                    k.ReadProcessMemory(h,C.c_void_p(pos),buffer,amount,C.byref(got))
                    if got.value:
                        blob=tail+buffer.raw[:got.value]
                        for pattern,kind in patterns:
                            off=blob.find(pattern)
                            while off>=0:
                                candidate=pos-len(tail)+off
                                if kind=='free' and valid(candidate):candidates.add(candidate)
                                if kind=='motion':mover_candidates.add(candidate)
                                off=blob.find(pattern,off+1)
                        tail=blob[-7:]
                    else:tail=b''
                    pos+=amount
                    if time.monotonic()-t0>120:raise RuntimeError('Object search timed out; no writes performed.')
            if not args.address:
                if len(candidates)!=1:raise RuntimeError(f'Expected one live Free camera; found {len(candidates)}. Enter Photo Mode, select Free, then retry.')
                obj=candidates.pop()
        if args.mover_address:
            if not valid_mover(args.mover_address):raise RuntimeError('Motion object type or owner mismatch.')
            mover=args.mover_address
        else:
            mover_candidates={x for x in mover_candidates if valid_mover(x)}
            if len(mover_candidates)!=1:raise RuntimeError(f'Expected one matching movement controller; found {len(mover_candidates)}. No writes performed.')
            mover=mover_candidates.pop()
        previous,mover_previous=validated_snapshot(obj,mover);values=struct.unpack('<4f',previous)
        mover_values={name:struct.unpack('<f',data)[0] for name,data in mover_previous.items()}
        if args.inspect_only:
            state='read-only verified';status();print(json.dumps({'object':hex(obj),'values':values,'mover':hex(mover),'mover_values':mover_values}));return
        expected=previous;mover_expected=dict(mover_previous);start=time.monotonic();last_status=0
        print(f'Native Photo Mode helper active: {args.normal:g}x normally, {args.boost:g}x while Shift is held. Ctrl+Alt+F10 stops it.',flush=True)
        while time.monotonic()-start<args.minutes*60:
            exitcode=W.DWORD()
            if not k.GetExitCodeProcess(h,C.byref(exitcode)) or exitcode.value!=259:state='game exited';break
            if (OUT/'stop-boost.request').exists():state='stop requested';break
            if all(u.GetAsyncKeyState(key)&0x8000 for key in [0x11,0x12,0x79]):state='stop hotkey';break
            if not valid(obj) or not valid_mover(mover):
                # A recreated Photo Mode camera gets its own baseline snapshot.
                # Never reuse the previous object's addresses or write into a freed slot.
                state='waiting for recreated Free camera';status()
                try:
                    if valid(obj) and read(obj+DATA_OFFSET+8,16)==expected:write(obj+DATA_OFFSET+8,previous)
                except RuntimeError:pass
                pair=find_nearby(obj)
                if pair is None:time.sleep(.25);continue
                new_obj,new_mover=pair
                try:new_previous,new_mover_previous=validated_snapshot(new_obj,new_mover)
                except RuntimeError:time.sleep(.25);continue
                obj,mover=new_obj,new_mover;previous=new_previous;expected=previous
                mover_previous=new_mover_previous;mover_expected=dict(mover_previous)
                state='reattached';status();print(f'Reattached to recreated Free camera {hex(obj)}',flush=True)
            try:
                current=read(obj+DATA_OFFSET+8,16)
                motion_changed=any(read(mover+MOTION_FIELDS[name],4)!=data for name,data in mover_expected.items())
            except RuntimeError:
                if not valid(obj) or not valid_mover(mover):continue
                raise
            if current!=expected or motion_changed:
                # Deallocation can occur between the type check and the value read.
                # Recheck before treating this as a change to a still-live object.
                if not valid(obj) or not valid_mover(mover):continue
                state='live camera values changed externally; stopped safely';break
            foreground=W.DWORD();u.GetWindowThreadProcessId(u.GetForegroundWindow(),C.byref(foreground))
            boosted=foreground.value==args.pid and bool(u.GetAsyncKeyState(0x10)&0x8000)
            multiplier=args.boost if boosted else args.normal
            wanted=struct.pack('<4f',1000.0,2*multiplier,multiplier,1000*multiplier)
            if not valid(obj) or not valid_mover(mover):continue
            if current!=wanted:write(obj+DATA_OFFSET+8,wanted);expected=wanted
            wanted_motion={'tether':1000.0,'move':2*multiplier,'rise':multiplier,'acceleration':1000*multiplier}
            for name,value in wanted_motion.items():
                data=struct.pack('<f',value)
                if data!=mover_expected[name]:
                    if not valid(obj) or not valid_mover(mover):break
                    write(mover+MOTION_FIELDS[name],data);mover_expected[name]=data
            newstate='boost' if boosted else 'normal'
            if state!=newstate or time.monotonic()-last_status>2:
                state=newstate;status();last_status=time.monotonic()
            time.sleep(0.01)
        else:state='session time limit reached'
    finally:
        if mover_previous and mover_expected and mover is not None:
            try:
                if valid_mover(mover):
                    for name,data in mover_previous.items():
                        if read(mover+MOTION_FIELDS[name],4)==mover_expected[name]:write(mover+MOTION_FIELDS[name],data)
            except Exception as e:state+='; movement restoration unavailable: '+str(e)
        if previous is not None and expected is not None and obj is not None:
            try:
                if valid(obj) and read(obj+DATA_OFFSET+8,16)==expected:
                    write(obj+DATA_OFFSET+8,previous);restored=True
            except Exception as e:state+='; restoration unavailable: '+str(e)
        try:status()
        except Exception:pass
        k.CloseHandle(h)
    print(f'Helper stopped: {state}; previous values restored={restored}',flush=True)

if __name__=='__main__':
    try:main()
    except Exception as e:
        print(f'Camera helper refused/stopped: {e}',file=sys.stderr,flush=True);sys.exit(1)
