"""Read-only disassembly with chained x64 unwind fragments resolved."""
import bisect
import runpy
import struct
import sys
from pathlib import Path

r = runpy.run_path(str(Path(__file__).with_name('disassemble_camera.py')))
starts = [row[0] for row in r['PDATA']]
fmt = r['Formatter'](r['FormatterSyntax'].NASM)

def row_at(address):
    index = bisect.bisect_right(starts, address) - 1
    if index >= 0 and r['PDATA'][index][0] <= address < r['PDATA'][index][1]:
        return r['PDATA'][index]
    return None

def root(row):
    seen = set()
    while row and row not in seen:
        seen.add(row)
        header = r['bytes_at'](row[2], 4)
        if not (header[0] >> 3) & 4:
            break
        tail = (4 + header[2] * 2 + 3) & ~3
        row = struct.unpack('<III', r['bytes_at'](row[2] + tail, 12))
    return row

roots = {row: root(row) for row in r['PDATA']}

def ranges(address):
    row = row_at(address)
    if row is None:
        return [(address, address + 128, 0)]
    owner = roots[row]
    return [x for x in r['PDATA'] if roots[x] == owner]

def instructions(address):
    for begin, end, unwind in ranges(address):
        yield from r['Decoder'](64, r['bytes_at'](begin, end - begin), ip=begin)

def dump(address):
    print('FUNCTION', hex(address), 'ROOT', root(row_at(address)), 'RANGES', ranges(address))
    for instruction in instructions(address):
        print(f'{instruction.ip:08X} {fmt.format(instruction)}')

def refs(address, kind):
    name = 'branch-refs.bin' if kind == 'branch' else 'rip-refs.bin'
    for target, ip, size in struct.iter_unpack('<3I', Path(__file__).with_name(name).read_bytes()):
        if target == address:
            row = root(row_at(ip))
            ins = next(iter(r['Decoder'](64, r['bytes_at'](ip, size), ip=ip)))
            print(hex(target), hex(ip), 'ROOT', hex(row[0]) if row else None, fmt.format(ins))

def datarefs(address):
    needle = struct.pack('<Q', r['BASE'] + address)
    for name, va, vs, rp, rs in r['SECTIONS']:
        if name not in (b'.rdata', b'.data'):
            continue
        position = r['DATA'].find(needle, rp, rp + rs)
        while position >= 0:
            print('POINTER', hex(va + position - rp))
            position = r['DATA'].find(needle, position + 1, rp + rs)

def nearrefs(address):
    for target, ip, size in struct.iter_unpack('<3I', Path(__file__).with_name('rip-refs.bin').read_bytes()):
        if address - 32 <= target <= address + 32:
            row = root(row_at(ip))
            ins = next(iter(r['Decoder'](64, r['bytes_at'](ip, size), ip=ip)))
            print(hex(target), hex(ip), 'ROOT', hex(row[0]) if row else None, fmt.format(ins))

if __name__ == '__main__':
    for value in sys.argv[2:]:
        address = int(value, 0)
        if sys.argv[1] == 'dump':
            dump(address)
        elif sys.argv[1] == 'data':
            datarefs(address)
        elif sys.argv[1] == 'near':
            nearrefs(address)
        else:
            refs(address, sys.argv[1])
