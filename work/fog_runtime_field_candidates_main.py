from collections import defaultdict
from native_trace_full import r, row_at, roots, fmt

groups = defaultdict(list)
for name, va, vs, rp, rs in r['SECTIONS']:
    if name != b'.text':
        continue
    for instruction in r['Decoder'](64, r['DATA'][rp:rp+rs], ip=va):
        if instruction.memory_base and instruction.memory_displacement in (0x43C,0x440,0x444,0x448,0x44C,0x450,0x454):
            row = row_at(instruction.ip)
            if row:
                groups[roots[row][0]].append((instruction.memory_base,instruction.memory_displacement,instruction.ip,fmt.format(instruction)))

for address, items in sorted(groups.items()):
    for base in {x[0] for x in items}:
        offsets = {x[1] for x in items if x[0] == base}
        if {0x44C,0x450} <= offsets and len(offsets) >= 4:
            print('FUNCTION',hex(address),'FIELDS',','.join(hex(x) for x in sorted(offsets)))
            for b, off, ip, label in items:
                if b == base:
                    print(f'{ip:08X} {label}')
