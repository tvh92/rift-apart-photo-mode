"""Generate isolated native type4 fade/distance/unwind bytes from exact build."""
from pathlib import Path
import hashlib,struct
from native_trace_full import r,ranges
assert hashlib.sha256(r['DATA']).hexdigest()=='51299faca61866cf10ea9035a15b8f22600a56557dd5ffc1aad390d5a54e6d82'
lines=['/* Generated exact-build native specular helper fixture. */']
def array(name,data):lines.append('static const unsigned char '+name+'[]={' + ','.join(hex(x) for x in data)+'};')
rows=[];fills=[];constants={}
for address in (0x1098f90,0x389950):
    parts=ranges(address);rows.extend(parts)
    code=r['bytes_at'](address,parts[-1][1]-address)
    name='spec_code_'+hex(address)[2:];array(name,code)
    fills.append(f'memcpy((void*)(base+{hex(address)}),{name},sizeof({name}));')
    for ins in r['Decoder'](64,code,ip=address):
        if ins.is_ip_rel_memory_operand:constants[ins.ip_rel_memory_address]=r['bytes_at'](ins.ip_rel_memory_address,16)
    for i,part in enumerate(parts):
        h=r['bytes_at'](part[2],4);n=(4+2*h[2]+3)&~3
        if(h[0]>>3)&4:n+=12
        assert h[0] in (1,0x21)
        name=f'spec_unwind_{address:x}_{i}';array(name,r['bytes_at'](part[2],n))
        fills.append(f'memcpy((void*)(base+{hex(part[2])}),{name},sizeof({name}));')
for address,data in constants.items():
    name=f'spec_constant_{address:x}';array(name,data)
    fills.append(f'memcpy((void*)(base+{hex(address)}),{name},sizeof({name}));')
lines.append('static RUNTIME_FUNCTION spec_native_rows[]={' + ','.join('{'+','.join(hex(x) for x in row)+'}' for row in sorted(rows))+'};')
lines.append('static void fill_type4_fixture(uintptr_t base){' + '\n'.join(fills)+'}')
Path('work/native-abi/PhotoType4Fixture.h').write_text('\n'.join(lines)+'\n')
print('Type4 aligned call window:',r['bytes_at'](0x10be260,8).hex())
print('Native type4 and distance fixtures generated:',len(rows),'unwind fragments.')
