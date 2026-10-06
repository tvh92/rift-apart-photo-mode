"""Execute isolated exact-build native light maths and an experimental branch copy.

No game process is opened or changed. This validates local arithmetic only;
it is not a production hook, registered unwind implementation, or GPU proof.
"""
import ctypes as C
from ctypes import wintypes as W
import hashlib,json,math,struct
from pathlib import Path
from native_trace_full import r,ranges

START=0x1099200
EXPECTED='51299faca61866cf10ea9035a15b8f22600a56557dd5ffc1aad390d5a54e6d82'
assert hashlib.sha256(r['DATA']).hexdigest()==EXPECTED
parts=ranges(START)
assert parts[0][0]==START and all(parts[i][1]==parts[i+1][0] for i in range(len(parts)-1))
END=parts[-1][1]
original=r['bytes_at'](START,END-START)
assert original[0xBD:0xBF]==bytes.fromhex('0f83')
decoder=r['Decoder'](64,original,ip=START)
rip=[]
for ins in decoder:
    if ins.is_ip_rel_memory_operand:
        offsets=decoder.get_constant_offsets(ins)
        assert offsets.displacement_size==4
        rip.append((ins.ip-START,ins.len,offsets.displacement_offset,ins.ip_rel_memory_address))
    assert 'call' not in r['Formatter'](r['FormatterSyntax'].NASM).format(ins).lower()
assert set(x[3] for x in rip)=={0x53394EC,0x4A4A198,0x2E70488,0x2E69860,0x2E6D030}
k=C.WinDLL('kernel32',use_last_error=True)
k.VirtualAlloc.argtypes=[C.c_void_p,C.c_size_t,W.DWORD,W.DWORD];k.VirtualAlloc.restype=C.c_void_p
k.VirtualProtect.argtypes=[C.c_void_p,C.c_size_t,W.DWORD,C.POINTER(W.DWORD)];k.VirtualProtect.restype=W.BOOL
k.VirtualFree.argtypes=[C.c_void_p,C.c_size_t,W.DWORD];k.VirtualFree.restype=W.BOOL
base=k.VirtualAlloc(None,0x4000,0x3000,4)
if not base:raise C.WinError(C.get_last_error())
try:
    targets={value:base+0x2000+16*index for index,value in enumerate(sorted(set(x[3] for x in rip)))}
    for target,address in targets.items():
        value=b'\0\0\0\0' if target==0x53394EC else r['bytes_at'](target,4)
        C.memmove(address,value,4)
    for relative in (0,0x1000):
        code=bytearray(original)
        for offset,length,displacement,target in rip:
            struct.pack_into('<i',code,offset+displacement,targets[target]-(base+relative+offset+length))
        if relative:
            # Same six-byte length/end/target; skip only far-RGB fading.
            code[0xBD:0xBF]=b'\x90\xe9'
        C.memmove(base+relative,bytes(code),len(code))
    old=W.DWORD()
    if not k.VirtualProtect(base,0x2000,0x20,C.byref(old)):raise C.WinError(C.get_last_error())
    fn=C.WINFUNCTYPE(None,C.c_void_p,C.c_float,C.c_float,C.c_void_p,C.c_void_p,C.c_void_p)
    native,photo=fn(base),fn(base+0x1000)
    light=C.create_string_buffer(0x170)
    for offset,value in ((0x98,-.5),(0x9C,.01),(0xA0,100),(0xA4,70),
                         (0xA8,.2),(0xAC,.4),(0xB0,.6),(0xC8,.7),(0xCC,75)):
        struct.pack_into('<f',light,offset,value)
    def evaluate(function,flags,front,centre):
        struct.pack_into('<I',light,0x88,flags)
        rgb=(C.c_float*3)();scalar=C.c_float();kind=C.c_uint()
        function(light,front,centre,rgb,C.byref(scalar),C.byref(kind))
        return [*rgb,scalar.value,kind.value]
    def same(a,b):
        return all(math.isclose(x,y,abs_tol=2e-7,rel_tol=2e-6) for x,y in zip(a,b))
    cases=0
    for start in (0,70):
        struct.pack_into('<f',light,0xA4,start)
        for debug in (0,1):
            C.c_ubyte.from_address(targets[0x53394EC]).value=debug
            for near in (0,1<<19):
                for shadow in (0,1<<20):
                    for kind in (0,2):
                        for front in (0,60,85,100,200):
                            for centre in (25,80,150):
                                flags=kind|16|near|shadow
                                expected=evaluate(native,flags,front,centre)
                                actual=evaluate(photo,flags|(1<<18),front,centre)
                                assert same(expected,actual),(start,debug,flags,front,centre,expected,actual)
                                # Native behavior for lights with far flag off is unchanged.
                                assert same(expected,evaluate(photo,flags,front,centre))
                                cases+=1
    struct.pack_into('<f',light,0xA4,70)
    C.c_ubyte.from_address(targets[0x53394EC]).value=0
    faded=evaluate(native,1<<18,85,80)
    retained=evaluate(photo,1<<18,85,80)
    assert same(faded[:3],[.1,.2,.3]) and same(retained[:3],[.2,.4,.6])
    report={'exe_sha256':EXPECTED,'function_rva':hex(START),'function_bytes':len(original),
            'isolated_cases_passed':cases,'changed_original_instruction':'JAE1099366 -> unconditional same-target jump at10992BD',
            'example_native_RGB':faded[:3],'example_retained_RGB':retained[:3],
            'preserved':'Native near fading, separate scalar/type outputs, debug multiplier and no-far-flag behavior match.',
            'limitations':'No live process or installed changes. Full GPU consumer and production relocation/unwind/gates are not established.'}
    Path('work/native-light-far-fade-isolated-test.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
finally:
    k.VirtualFree(base,0,0x8000)
