"""Read a bounded saved AMD64 minidump; stack words are not unwound frames."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

def inspect(path):
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError('Dump exceeds this bounded reader limit.')
    data = path.read_bytes()
    def read(offset, size):
        if offset < 0 or size < 0 or offset + size > len(data):
            raise ValueError('Dump offset outside file.')
        return data[offset:offset + size]
    def unpack(fmt, offset):
        return struct.unpack(fmt, read(offset, struct.calcsize(fmt)))
    if read(0, 4) != b'MDMP':
        raise ValueError('Not a minidump.')
    count, directory = unpack('<II', 8)
    if count > 128:
        raise ValueError('Unbounded stream count.')
    streams = {}
    for index in range(count):
        kind, size, rva = unpack('<III', directory + index * 12)
        read(rva, size)
        streams[kind] = (rva, size)
    modules = []
    if 4 in streams:
        rva, size = streams[4]
        n, = unpack('<I', rva)
        if n > 512 or 4 + n * 108 > size:
            raise ValueError('Unbounded module list.')
        for index in range(n):
            base, image_size, checksum, timestamp, name_rva = unpack('<QIIII', rva + 4 + index * 108)
            length, = unpack('<I', name_rva)
            if length > 32768:
                raise ValueError('Unbounded module name.')
            name = read(name_rva + 4, length).decode('utf-16-le', errors='replace').replace('\\', '/').rsplit('/', 1)[-1]
            modules.append({'name': name, 'base': base, 'size': image_size, 'timestamp': timestamp})
    def resolve(value):
        for module in modules:
            if module['base'] <= value < module['base'] + module['size']:
                return module['name'] + '+' + hex(value - module['base'])
        return None
    ranges = []
    if 5 in streams:
        rva, size = streams[5]
        n, = unpack('<I', rva)
        if n > 65536 or 4 + n * 16 > size:
            raise ValueError('Unbounded memory list.')
        for index in range(n):
            address, amount, offset = unpack('<QII', rva + 4 + index * 16)
            read(offset, amount)
            ranges.append((address, amount, offset))
    if 3 in streams:
        rva, size = streams[3]
        n, = unpack('<I', rva)
        if n > 1024 or 4 + n * 48 > size:
            raise ValueError('Unbounded thread list.')
        for index in range(n):
            address, amount, offset = unpack('<QII', rva + 4 + index * 48 + 24)
            read(offset, amount)
            ranges.append((address, amount, offset))
    report = {'source': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
              'streams': sorted(streams), 'writes': 0,
              'limits': 'Stack words are candidates, not an unwound call stack. No symbols downloaded.',
              'project_modules': [{**module, 'base': hex(module['base'])} for module in modules
                                  if module['name'].lower() in ('riftapart.exe', 'hid.dll')]}
    # Extract only the embedded renderer error, not arbitrary strings from
    # saved process memory. This preserves the HRESULT beside the exception.
    report['embedded_nri_errors'] = [match.group().decode('ascii') for match in
        re.finditer(rb'\[nri\([^\x00-\x1f]{1,32}\)::ERROR\][\x20-\x7e]{0,480}', data)][:8]
    if 6 not in streams:
        report['exception'] = None
        return report
    rva, size = streams[6]
    if size < 168:
        raise ValueError('Incomplete exception stream.')
    thread, = unpack('<I', rva)
    code, flags, record, address, params, unused = unpack('<IIQQII', rva + 8)
    context_size, context_rva = unpack('<II', rva + 160)
    if not 256 <= context_size <= 65536:
        raise ValueError('Incomplete/unbounded AMD64 context.')
    context = read(context_rva, context_size)
    registers = {name: struct.unpack_from('<Q', context, offset)[0] for name, offset in
                 [('rax',120),('rcx',128),('rdx',136),('rbx',144),('rsp',152),('rbp',160),
                  ('rsi',168),('rdi',176),('r8',184),('r9',192),('r10',200),('r11',208),
                  ('r12',216),('r13',224),('r14',232),('r15',240),('rip',248)]}
    report['exception'] = {'thread': thread, 'code': hex(code), 'address': hex(address),
                           'address_module': resolve(address), 'context_rip': hex(registers['rip']),
                           'context_rip_module': resolve(registers['rip']),
                           'registers': {name:hex(value) for name,value in registers.items()}}
    stack = b''
    for start, amount, offset in ranges:
        if start <= registers['rsp'] < start + amount:
            skip = registers['rsp'] - start
            stack = read(offset + skip, min(amount - skip, 4096))
            break
    candidates = []
    for offset in range(0, len(stack) - 7, 8):
        value, = struct.unpack_from('<Q', stack, offset)
        module = resolve(value)
        if module:
            candidates.append({'stack_offset': hex(offset), 'address':hex(value), 'module':module})
    report['stack_bytes_read'] = len(stack)
    report['mapped_stack_candidates'] = candidates[:100]
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dumps', nargs='+', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = [inspect(path) for path in args.dumps]
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + '\n')
    for item in report:
        print(json.dumps({key:value for key,value in item.items() if key != 'mapped_stack_candidates'}))
        print(json.dumps({'stack_candidates_first_24':item.get('mapped_stack_candidates',[])[:24]}))
