"""Read-only camera-value reconnaissance. No writes, hooks, or injection."""
import ctypes as C, struct, itertools, json, argparse, time
from ctypes import wintypes as W
from pathlib import Path

class MBI(C.Structure):
    _fields_=[('BaseAddress',C.c_void_p),('AllocationBase',C.c_void_p),('AllocationProtect',W.DWORD),
              ('PartitionId',W.WORD),('RegionSize',C.c_size_t),('State',W.DWORD),('Protect',W.DWORD),('Type',W.DWORD)]

def configure():
    k=C.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
    k.CloseHandle.argtypes=[W.HANDLE]
    k.VirtualQueryEx.argtypes=[W.HANDLE,C.c_void_p,C.POINTER(MBI),C.c_size_t];k.VirtualQueryEx.restype=C.c_size_t
    k.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];k.ReadProcessMemory.restype=W.BOOL
    k.QueryFullProcessImageNameW.argtypes=[W.HANDLE,W.DWORD,W.LPWSTR,C.POINTER(W.DWORD)];k.QueryFullProcessImageNameW.restype=W.BOOL
    return k

def main():
    ap=argparse.ArgumentParser();ap.add_argument('pid',type=int);ap.add_argument('--output',default='work/camera-memory-readonly.json')
    args=ap.parse_args();k=configure();h=k.OpenProcess(0x1010,False,args.pid)
    if not h:raise C.WinError(C.get_last_error())
    try:
        path=C.create_unicode_buffer(32768);size=W.DWORD(len(path))
        if not k.QueryFullProcessImageNameW(h,0,path,C.byref(size)):raise C.WinError(C.get_last_error())
        expected=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\RiftApart.exe')
        assert Path(path.value).resolve()==expected.resolve(),'Unexpected process'
        patterns={}
        for values in itertools.permutations([1000.0,20.0,10.0,10000.0]):patterns[struct.pack('<4f',*values)]=list(values)
        # Same values in the serialized DAT1 representation.
        patterns[struct.pack('<4H',10000,10,20,1000)]='serialized CamData tail'
        # Some native implementations may place the three motion values together.
        for values in itertools.permutations([20.0,10.0,10000.0]):patterns[struct.pack('<3f',*values)]=list(values)
        result=[];address=0;scanned=0;regions=0;t0=time.monotonic();buffer=C.create_string_buffer(4*1024*1024)
        pointer_patterns = [(struct.pack('<Q',0x7ff6903f0000+rva),label) for rva,label in
            [(0x4690a50,'FreeMoveCamData vtable'),(0x45fd8b0,'PhotomodeCameraFreeMove vtable'),
             (0x45fdef0,'PhotomodeCameraMotionFly vtable'),(0x4690b30,'PhotomodeCameraFreeMovePrius vtable')]]
        while address<0x7FFFFFFF0000:
            info=MBI()
            if not k.VirtualQueryEx(h,C.c_void_p(address),C.byref(info),C.sizeof(info)):break
            base=info.BaseAddress or 0;end=base+info.RegionSize
            if end<=address:break
            address=end
            if info.Type != 0x20000 or info.State!=0x1000 or info.Protect&0x100 or (info.Protect&0xff) not in [4,8,0x40,0x80]:continue
            if info.RegionSize > 256*1024*1024: continue
            regions+=1;pos=base;tail=b''
            while pos<end:
                amount=min(len(buffer),end-pos);got=C.c_size_t()
                ok=k.ReadProcessMemory(h,C.c_void_p(pos),buffer,amount,C.byref(got))
                if got.value:
                    data=tail+buffer.raw[:got.value];origin=pos-len(tail)
                    # Search the precise native type pointer and the rare acceleration
                    # value once per chunk, rather than 48 complete float patterns.
                    for pattern,label in pointer_patterns:
                        off=data.find(pattern)
                        while off>=0:
                            if off+len(pattern)>len(tail):
                                result.append({'address':hex(origin+off),'pattern':label,'region_base':hex(base),'region_size':info.RegionSize,
                                               'protect':hex(info.Protect),'type':hex(info.Type),
                                               'context_hex':data[max(0,off-32):off+len(pattern)+96].hex()})
                            off=data.find(pattern,off+1)
                    tail=data[-64:];scanned+=got.value
                else:tail=b''
                pos+=amount
                if time.monotonic()-t0>90: break
            if time.monotonic()-t0>90: break
        payload={'pid':args.pid,'process':path.value,'bytes_scanned':scanned,'regions':regions,'seconds':time.monotonic()-t0,'matches':result}
        Path(args.output).write_text(json.dumps(payload,indent=2));print(json.dumps({k:v for k,v in payload.items() if k!='matches'},indent=2))
        print('Camera type matches:',len(result))
    finally:k.CloseHandle(h)

if __name__=='__main__':main()
