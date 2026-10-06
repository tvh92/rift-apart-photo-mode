"""Generate isolated native light-filter cutoff bytes/unwind from exact build.

Copies the real 0x10B9A50 job window 0x10B9BDD..0x10B9C41 (bit18 far cutoff
and bit19 near fade), its helpers 0x10B9750 and 0x389950, their RIP-relative
constants, and every unwind fragment of the three functions.
"""
from pathlib import Path
import hashlib
from native_trace_full import r, ranges
assert hashlib.sha256(r['DATA']).hexdigest() == '51299faca61866cf10ea9035a15b8f22600a56557dd5ffc1aad390d5a54e6d82'
WINDOW = (0x10B9BDD, 0x10B9C41)
lines = ['/* Generated exact-build native light-filter cutoff fixture. */']
def array(name, data):
    lines.append('static const unsigned char ' + name + '[]={' + ','.join(hex(x) for x in data) + '};')
rows, fills, constants = [], [], {}
def add_code(address, code):
    name = f'cut_code_{address:x}'
    array(name, code)
    fills.append(f'memcpy((void*)(base+{hex(address)}),{name},sizeof({name}));')
    for ins in r['Decoder'](64, code, ip=address):
        if ins.is_ip_rel_memory_operand:
            constants[ins.ip_rel_memory_address] = r['bytes_at'](ins.ip_rel_memory_address, 16)
for address, whole in ((0x10B9A50, False), (0x10B9750, True), (0x389950, True)):
    parts = ranges(address)
    rows.extend(parts)
    if whole:
        add_code(address, r['bytes_at'](address, parts[-1][1] - address))
    for i, part in enumerate(parts):
        h = r['bytes_at'](part[2], 4)
        n = (4 + 2 * h[2] + 3) & ~3
        if (h[0] >> 3) & 4:
            n += 12
        assert h[0] in (1, 0x21), hex(h[0])
        name = f'cut_unwind_{address:x}_{i}'
        array(name, r['bytes_at'](part[2], n))
        fills.append(f'memcpy((void*)(base+{hex(part[2])}),{name},sizeof({name}));')
add_code(WINDOW[0], r['bytes_at'](WINDOW[0], WINDOW[1] - WINDOW[0]))
for address, data in constants.items():
    name = f'cut_constant_{address:x}'
    array(name, data)
    fills.append(f'memcpy((void*)(base+{hex(address)}),{name},sizeof({name}));')
rows = sorted(set(rows))
lines.append(f'#define CUT_NATIVE_ROWS {len(rows)}')
lines.append('static RUNTIME_FUNCTION cut_native_rows[]={' + ','.join('{' + ','.join(hex(x) for x in row) + '}' for row in rows) + '};')
lines.append('static void fill_cutoff_fixture(uintptr_t base){' + '\n'.join(fills) + '}')
root = Path(__file__).resolve().parents[1]
(root / 'work/native-abi/PhotoCutoffFixture.h').write_text('\n'.join(lines) + '\n')
print('Cutoff aligned window 10B9C00:', r['bytes_at'](0x10B9C00, 16).hex())
print('Native rows:', [tuple(hex(x) for x in row) for row in rows])
