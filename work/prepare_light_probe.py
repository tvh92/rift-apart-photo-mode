"""Generate an isolated exact-executable native function/unwind fixture."""
from pathlib import Path
import hashlib,struct
from native_trace_full import r,ranges
assert hashlib.sha256(r['DATA']).hexdigest()=='51299faca61866cf10ea9035a15b8f22600a56557dd5ffc1aad390d5a54e6d82'
rows=ranges(0x1099200)
code=r['bytes_at'](0x1099200,rows[-1][1]-0x1099200)
assert code[0x70:0x78]==bytes.fromhex('f20f1081a8000000')
lines=['/* Generated from the hash-verified executable. */']
def array(name,data):
    lines.append('static const unsigned char '+name+'[] = {'+','.join(hex(x) for x in data)+'};')
array('light_native_code',code)
lines.append('static RUNTIME_FUNCTION light_native_rows[] = {'+','.join('{'+','.join(hex(x) for x in row)+'}' for row in rows)+'};')
for i,row in enumerate(rows):
    h=r['bytes_at'](row[2],4)
    n=(4+2*h[2]+3)&~3
    if (h[0]>>3)&4:n+=12
    assert h[0] in (1,0x21)
    array('light_unwind_'+str(i),r['bytes_at'](row[2],n))
lines.append('static void fill_native_fixture(uintptr_t base) {')
lines.append('memcpy((void*)(base+0x1099200),light_native_code,sizeof(light_native_code));')
for i,row in enumerate(rows):lines.append(f'memcpy((void*)(base+{hex(row[2])}),light_unwind_{i},sizeof(light_unwind_{i}));')
for addr in (0x53394EC,0x4A4A198,0x2E70488,0x2E69860,0x2E6D030):
    value=struct.unpack('<I',r['bytes_at'](addr,4))[0]
    lines.append(f'*(uint32_t*)(base+{hex(addr)})={hex(value)};')
lines.append('}')
Path('work/native-abi/PhotoLightFixture.h').write_text('\n'.join(lines)+'\n')
print('Native light fixture:637 bytes,5 unwind fragments,5 native constants.')
