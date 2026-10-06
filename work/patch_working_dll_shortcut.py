"""Change only two key constants in the verified working DLL; no relinking."""
from pathlib import Path
import hashlib, json

root=Path(__file__).resolve().parents[1]
native=root/'outputs/camera-native'
source=native/'backup/2026-10-05-before-control-indicator/hid.dll'
old=source.read_bytes()
baseline='7508bd33654d057202fbd91b8c81d8622dca1c1e781c21b52ce82023fa14b272'
assert hashlib.sha256(old).hexdigest()==baseline
# HookPhotoTick RVA2FD0. MOV ECX,key immediately precedes each call through
# the verified GetAsyncKeyState IAT entry at RVA2AE40. Change only imm8 bytes.
sites=[(0x23F2, bytes.fromhex('b912000000ff15437e0200'),0x12),
       (0x2402, bytes.fromhex('b94c000000ff15337e0200'),0x4C)]
new=bytearray(old)
for offset,expected,key in sites:
    assert old[offset:offset+len(expected)]==expected,hex(offset)
    assert old[offset+1]==key
    new[offset+1]=0x11
changed=[i for i,(a,b) in enumerate(zip(old,new)) if a!=b]
assert changed==[0x23F3,0x2403] and len(new)==len(old)
(native/'hid.dll').write_bytes(new)
report={'baseline_sha256':baseline,'dll_sha256':hashlib.sha256(new).hexdigest(),
        'only_changed_file_offsets':[hex(x) for x in changed],
        'changes':['VK_MENU -> VK_CONTROL','L -> VK_CONTROL'],
        'behavior':'Ctrl rising edge in focused active Photo Mode; baseline checks and three key probes retained.',
        'layout':'All other bytes, imports, relocations, exports, unwind metadata and addresses unchanged.'}
(root/'work/binary-ctrl-shortcut-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
