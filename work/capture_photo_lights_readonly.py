"""Read the proven primary-view light submission queues; no process writes.

Use only for a coordinated, stationary ordinary Photo Mode near/far capture.
Transient queues are sampled without stopping the renderer. Stable headers do
not make the entire capture atomic; missing/retired objects are reported.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import time
from capture_live_atmosphere import Module, EXE, EXPECTED, ROOT

DLL_HASHES = ('16dcd44057c3114b123e25974b9b563afc487650686d3985784614caba5f7cbd',  # lighting-v2
              'c4be06b9e069829ba3c173ab3545353f38de04d6a98c5f58533af42ae9efbe66')  # lighting-v3
DLL_HASH = DLL_HASHES[-1]
PRIMARY = 0x6739B10
PHOTO = 0x6138200
QUEUE = 0x1430
ARCHIVE = 0x67313C0
MAX_ENTRIES = 8192


def pointer(value):
    if not 0x10000 <= value < 0x800000000000 or value & 7:
        raise RuntimeError('Invalid or unaligned native pointer')
    return value


def queue_header(raw):
    if len(raw) != 16:
        raise RuntimeError('Incomplete queue header')
    address, identity, count, capacity = struct.unpack('<QIHH', raw)
    if count > capacity or capacity > 128:
        raise RuntimeError('Queue count/capacity outside native allocation bound')
    if count:
        pointer(address)
    return address, identity, count, capacity


def floats(raw, offset, count):
    result = struct.unpack_from('<' + 'f' * count, raw, offset)
    return [x if math.isfinite(x) else None for x in result]


def decode_record(raw):
    if len(raw) != 0x170:
        raise RuntimeError('Incomplete LightSubmit record')
    return {'world_position_B0': floats(raw, 0xB0, 3),
            'rgb_70': floats(raw, 0x70, 3), 'specular_7C': floats(raw, 0x7C, 1)[0],
            'attenuation_radius_DC': floats(raw, 0xDC, 1)[0],
            'depth_118_11C': floats(raw, 0x118, 2),
            'type_flags_100_10C_hex': raw[0x100:0x10C].hex(),
            'raw_hex': raw.hex()}


def source_summary(raw):
    if len(raw) != 0xD0:
        raise RuntimeError('Incomplete source prefix')
    return {'translation_30': floats(raw, 0x30, 3),
            'entity_flags_5C': hex(struct.unpack_from('<I', raw, 0x5C)[0]),
            'flags_88': hex(struct.unpack_from('<I', raw, 0x88)[0]),
            'view_mask_8C': hex(struct.unpack_from('<I', raw, 0x8C)[0]),
            'secondary_mask_90': hex(struct.unpack_from('<I', raw, 0x90)[0]),
            'raw_hex': raw.hex()}


def query_summary(read, address, view):
    pointer(address)
    raw = read(address, 0x90)
    if struct.unpack_from('<Q', raw)[0] != view:
        raise RuntimeError('Query belongs to another view')
    arrays = {}
    sources = {}
    # 10BB680/10BA710 input arrays and final selected array.
    for name, poff, coff, extra in (('input_fixed', 8, 0x10, None),
                                   ('input_optional', 0x18, 0x20, None),
                                   ('selected', 0x38, 0x40, 0x44)):
        count = struct.unpack_from('<i', raw, coff)[0]
        if extra is not None:
            count += struct.unpack_from('<i', raw, extra)[0]
        if not 0 <= count <= MAX_ENTRIES:
            raise RuntimeError('Unbounded light query count')
        arr = struct.unpack_from('<Q', raw, poff)[0]
        entries = read(pointer(arr), count * 8) if count else b''
        ids = []
        for item in struct.iter_unpack('<Q', entries):
            source = item[0]
            ids.append(hex(source))
            if hex(source) in sources:
                continue
            try:
                sources[hex(source)] = source_summary(read(pointer(source), 0xD0))
            except (OSError, RuntimeError) as error:
                sources[hex(source)] = {'error': str(error)}
        arrays[name] = {'count': count, 'pointers': ids}
        if count and read(arr, count * 8) != entries:
            raise RuntimeError('Query pointer array changed during sample')
    if read(address, 0x90) != raw:
        raise RuntimeError('Query header changed during sample')
    return {'pointer': hex(address), 'arrays': arrays, 'sources': sources,
            'limit': 'Source fields are not atomic; arrays/header were reread.'}


REGISTRIES = (0x6414C30, 0x64151D8)  # 107B760: request+64 bit0 clear/set
# 10BB786 stores the fixed key at query+70; 10BB83D the optional key at +68.
# Both keys come from 12B97E0 -> 107B750 -> 107B760. The slot's count pointer
# is query+10 (fixed) or query+20 (optional); output array is separate.
REQUEST_KINDS = (('fixed', 0x10, 8, 0x70), ('optional', 0x20, 0x18, 0x68))


def request_key_valid(key, registry_bit, index, generation):
    """107B8E4..107B907: key = generation<<32 | index*2 | registry bit."""
    return (key != 0 and key & 1 == registry_bit and
            (key & 0xFFFFFFFF) >> 1 == index and key >> 32 == generation)


def decode_planes(raw):
    """16-plane SoA shape (0x1600E30/0x1603D40): block i>>2 at +0x40*b,
    nx/ny/nz/d at +0/+0x10/+0x20/+0x30, lane i&3. Inside when n.p + d >= 0."""
    if len(raw) != 0x100:
        raise RuntimeError('Incomplete plane shape')
    planes = []
    for i in range(16):
        block, lane = (i >> 2) * 0x40, (i & 3) * 4
        planes.append(floats(raw, block + lane, 1) + floats(raw, block + 0x10 + lane, 1) +
                      floats(raw, block + 0x20 + lane, 1) + floats(raw, block + 0x30 + lane, 1))
    return planes


def view_clip(read, view):
    """Near/far fields used by 0x12121B0 and the six view planes (+2E0)."""
    raw = read(view + 0x2E0, 0x60)
    clip = read(view + 0x3F8, 0x40)
    near, far = struct.unpack_from('<2f', clip, 0)
    used, requested = struct.unpack_from('<2f', clip, 0x38)
    result = {'near_3F8': near, 'projection_far_3FC': far, 'far_430': used, 'requested_434': requested,
              'planes_2E0': [floats(raw, i * 16, 4) for i in range(6)]}
    holder = struct.unpack('<Q', read(view + 0x1BF0, 8))[0]
    result['obj_1BF0'] = hex(holder)
    if holder:
        result['obj_1BF0_170_174'] = floats(read(pointer(holder) + 0x170, 8), 0, 2)
    return result


def registry_stable(header, old_header, generation, old_generation):
    """Backing/capacity/generation fixed; count may only grow (lock inc 107B90E).

    Already-read slots are separately reread before acceptance, so appended
    requests do not invalidate them; a shrink or reallocation does.
    """
    backing, capacity, count = struct.unpack('<Qii', header)
    old_backing, old_capacity, old_count = struct.unpack('<Qii', old_header)
    return (generation == old_generation and backing == old_backing and
            capacity == old_capacity and old_count <= count <= capacity)


def registered_light_queries(read, base, view, diagnostics=None):
    """Typed query request slots, not a guessed world-LightDef catalog.

    A slot is accepted only when callback 12B8740, manager 674EC10, its
    generation/index/registry key, and the derived query's owner view and
    stored key all match. Request output (slot+68) is metadata only: 10BB270
    replaces query+8 and resets query+10 before filtering. That current count
    cannot bound the retired gather allocation. Only the query's current
    arrays are dereferenced; worker-output length/lifetime remain unproven.
    """
    results, errors = [], []
    by_query, registry_state = {}, []
    for registry_bit, registry in enumerate(REGISTRIES):
        header = read(base + registry + 0x508, 16)
        backing, capacity, count = struct.unpack('<Qii', header)
        generation_raw = read(base + registry + 0x598, 4)
        generation = struct.unpack('<I', generation_raw)[0]
        stats = {'registry_rva': hex(registry), 'count': count, 'capacity': capacity,
                 'generation': generation, 'callback_matches': 0, 'manager_matches': 0,
                 'key_matches': 0, 'owner_key_matches': 0, 'query_owner_candidates': []}
        if diagnostics is not None:
            diagnostics.append(stats)
        if not 0 <= count <= min(capacity, 2048):
            errors.append(f'Query registry count rejected: {count}/{capacity}')
            continue
        chunks = []
        if count:
            pointer(backing)
        # Each complete C0-byte slot stays within the per-read limit.
        for first in range(0, count, 512):
            n = min(512, count - first)
            address = backing + first * 0xC0
            chunks.append((first, address, read(address, n * 0xC0)))
        for first, address, data in chunks:
            for offset in range(0, len(data), 0xC0):
                slot = data[offset:offset + 0xC0]
                index = first + offset // 0xC0
                if struct.unpack_from('<Q', slot, 0x78)[0] != base + 0x12B8740:
                    continue
                stats['callback_matches'] += 1
                if struct.unpack_from('<Q', slot, 0x38)[0] != base + 0x674EC10:
                    continue
                stats['manager_matches'] += 1
                key = struct.unpack_from('<Q', slot)[0]
                if not request_key_valid(key, registry_bit, index, generation):
                    continue
                stats['key_matches'] += 1
                output, counter = (struct.unpack_from('<Q', slot, off)[0] for off in (0x68, 0x70))
                for kind, count_offset, array_offset, key_offset in REQUEST_KINDS:
                    query = counter - count_offset
                    try:
                        pointer(query)
                        head = read(query, 0x90)
                        owner = struct.unpack_from('<Q', head)[0]
                        stored = struct.unpack_from('<Q', head, key_offset)[0]
                        current = struct.unpack_from('<Q', head, array_offset)[0]
                        if len(stats['query_owner_candidates']) < 12:
                            stats['query_owner_candidates'].append({
                                'kind': kind, 'query': hex(query), 'owner': hex(owner),
                                'request_key': hex(key), 'query_key': hex(stored),
                                'request_output': hex(output), 'query_current_array': hex(current),
                                'output_equals_current': current == output,
                                'query_header_hex': head.hex(),
                                'request_slot': hex(address + offset), 'request_index': index,
                            })
                        if owner != view or stored != key:
                            continue
                        stats['owner_key_matches'] += 1
                        by_query.setdefault(query, []).append({
                            'kind': kind, 'registry_rva': hex(registry),
                            'slot_address': address + offset, 'slot': slot, 'key': key,
                            'output': output, 'count_offset': count_offset,
                            'key_offset': key_offset})
                        break
                    except (OSError, RuntimeError) as error:
                        if len(errors) < 12:
                            errors.append(str(error))
        # Request slots are immutable while active apart from work state.
        # Recheck ownership/generation; per-slot matching guards typed queries.
        if not registry_stable(read(base + registry + 0x508, 16), header,
                               read(base + registry + 0x598, 4), generation_raw):
            raise RuntimeError('Query registry ownership changed during sample')
        registry_state.append((registry, header, generation_raw))
    for query, requests in by_query.items():
        try:
            head = read(query, 0x90)
            # Revalidate the query token immediately before its arrays; the
            # earlier registry scan alone does not prove continued ownership.
            if struct.unpack_from('<Q', head)[0] != view or any(
                    struct.unpack_from('<Q', head, req['key_offset'])[0] != req['key']
                    for req in requests):
                raise RuntimeError('Light query ownership changed before array reads')
            result = query_summary(read, query, view)
            if read(query, 0x90) != head:
                raise RuntimeError('Query header changed during sample')
            result['requests'] = []
            for request in requests:
                out = {'pointer': hex(request['output']), 'read': False,
                       'reason': 'Gather allocation count and lifetime not proven; current query count cannot bound it.'}
                if read(request['slot_address'], 0xC0) != request['slot']:
                    raise RuntimeError('Light query request changed during sample')
                shape_ptr = struct.unpack_from('<Q', request['slot'], 0x48)[0]
                shape = decode_planes(read(pointer(shape_ptr), 0x100))
                result['requests'].append({
                    'shape_48': hex(shape_ptr), 'planes': shape,
                    'kind': request['kind'], 'registry_rva': request['registry_rva'],
                    'slot': hex(request['slot_address']), 'key': hex(request['key']),
                    'worker_output': out})
            if read(query, 0x90) != head:
                raise RuntimeError('Query header changed during sample')
            result['labels'] = {'arrays': 'Current query arrays: 10BA710 ranking input/selection.',
                                'worker_output': 'Request slot+68 metadata only; allocation not dereferenced.'}
            results.append(result)
        except (OSError, RuntimeError) as error:
            if len(errors) < 12:
                errors.append(str(error))
    for registry, header, generation_raw in registry_state:
        if not registry_stable(read(base + registry + 0x508, 16), header,
                               read(base + registry + 0x598, 4), generation_raw):
            raise RuntimeError('Query registry ownership changed during sample')
    return results, errors


def sample(read, base):
    photo = read(base + PHOTO, 0x58)
    if (struct.unpack_from('<Q', photo)[0] != base + 0x2FBF630 or
            struct.unpack_from('<i', photo, 0x50)[0] != 4 or photo[0x54] != 1):
        raise RuntimeError('Not active ordinary Photo Mode')
    view_word = read(base + PRIMARY, 8)
    view = pointer(struct.unpack('<Q', view_word)[0])
    position = read(view + 0x30, 12)
    header = read(view + QUEUE, 16)
    current, identity, count, _ = queue_header(header)
    archived = read(base + ARCHIVE, 16)
    arch_ptr, arch_count, arch_capacity = struct.unpack('<Qii', archived)
    # Bound the populated descriptors actually read, not the renderer's larger
    # unused allocation (this build reserves16384 descriptors in the live run).
    if not 0 <= arch_count <= min(arch_capacity, MAX_ENTRIES):
        raise RuntimeError(f'Unbounded renderer archive count: count={arch_count}, capacity={arch_capacity}')
    descriptors = read(pointer(arch_ptr), arch_count * 16) if arch_count else b''
    segments = []
    for segment_ptr, segment_count, segment_id in struct.iter_unpack('<QII', descriptors):
        if segment_id == identity:
            if not 0 < segment_count <= 128:
                raise RuntimeError('Invalid archived segment count')
            segments.append((pointer(segment_ptr), segment_count))
    if count:
        segments.append((current, count))
    if sum(n for _, n in segments) > MAX_ENTRIES:
        raise RuntimeError('Unbounded total primary queue entries')
    segment_data = [(p, read(p, n * 16)) for p, n in segments]
    records, queries, errors = [], [], []
    for p, data in segment_data:
        for packed_key, param in struct.iter_unpack('<QQ', data):
            pass_id = packed_key >> 48
            if pass_id != 0x67:
                continue
            try:
                pointer(param)
                item = decode_record(read(param, 0x170))
                item.update(pointer=hex(param), packed_key=hex(packed_key))
                records.append(item)
            except (OSError, RuntimeError) as error:
                errors.append({'pass': hex(pass_id), 'pointer': hex(param), 'error': str(error)})
    for p, data in segment_data:
        if read(p, len(data)) != data:
            raise RuntimeError('Submission queue changed during sample')
    if (read(view + QUEUE, 16) != header or read(base + ARCHIVE, 16) != archived or
            (arch_count and read(arch_ptr, len(descriptors)) != descriptors) or
            read(base + PRIMARY, 8) != view_word or read(view + 0x30, 12) != position or
            read(base + PHOTO, 0x58) != photo):
        raise RuntimeError('Photo/view/queue ownership changed during sample')
    # Separate snapshot: queue and queries need not come from the same frame.
    try:
        clip = view_clip(read, view)
    except (OSError, RuntimeError) as error:
        clip = {'error': str(error)}
    request_diagnostics = []
    queries, request_errors = registered_light_queries(read, base, view, request_diagnostics)
    if (read(base + PRIMARY, 8) != view_word or read(view + 0x30, 12) != position or
            read(base + PHOTO, 0x58) != photo):
        raise RuntimeError('Photo/view ownership changed during query snapshot')
    return {'view': hex(view), 'position_30': floats(position, 0, 3), 'view_clip': clip,
            'queue_identity': identity, 'segments': len(segments),
            'pass67_record_count': len(records), 'records': records,
            'queries': queries, 'errors': errors,
            'request_errors': request_errors,
            'request_diagnostics': request_diagnostics,
            'query_limit': 'Typed request registry only; source/query fields are non-atomic. Empty passBB marker is not used.',
            'atomic': False, 'callback_order_proven': False,
            'limit': 'Transient CPU submissions only; queue order is not final callback order. Absence or >512 does not establish the cause of lost illumination.'}


def capture(pid, seconds, sample_limit=6, interval_ms=40):
    if not 1 <= seconds <= 10 or not 1 <= sample_limit <= 32 or not 40 <= interval_ms <= 1000:
        raise ValueError('Capture bounds exceeded')
    if hashlib.sha256(EXE.read_bytes()).hexdigest() != EXPECTED:
        raise RuntimeError('Unsupported executable')
    if hashlib.sha256(EXE.with_name('hid.dll').read_bytes()).hexdigest() not in DLL_HASHES:
        raise RuntimeError('Unexpected mod DLL')
    k = C.WinDLL('kernel32', use_last_error=True)
    k.OpenProcess.argtypes, k.OpenProcess.restype = [W.DWORD, W.BOOL, W.DWORD], W.HANDLE
    k.CloseHandle.argtypes = [W.HANDLE]
    k.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD)]
    k.ReadProcessMemory.argtypes = [W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)]
    k.ReadProcessMemory.restype = W.BOOL
    k.CreateToolhelp32Snapshot.argtypes, k.CreateToolhelp32Snapshot.restype = [W.DWORD, W.DWORD], W.HANDLE
    k.Module32FirstW.argtypes = [W.HANDLE, C.POINTER(Module)]
    k.Module32NextW.argtypes = [W.HANDLE, C.POINTER(Module)]
    handle = k.OpenProcess(0x1010, False, pid)
    if not handle:
        raise C.WinError(C.get_last_error())
    try:
        name, size = C.create_unicode_buffer(32768), W.DWORD(32768)
        if not k.QueryFullProcessImageNameW(handle, 0, name, C.byref(size)):
            raise C.WinError(C.get_last_error())
        if Path(name.value).resolve() != EXE.resolve():
            raise RuntimeError('Unexpected process path')
        snap = k.CreateToolhelp32Snapshot(0x18, pid)
        if snap in (None, C.c_void_p(-1).value):
            raise C.WinError(C.get_last_error())
        base = None
        try:
            entry = Module()
            entry.dwSize = C.sizeof(entry)
            ok = k.Module32FirstW(snap, C.byref(entry))
            while ok:
                if entry.szModule.lower() == 'riftapart.exe':
                    base = entry.modBaseAddr
                    break
                ok = k.Module32NextW(snap, C.byref(entry))
        finally:
            k.CloseHandle(snap)
        if not base:
            raise RuntimeError('Executable module not found')

        def read(address, amount):
            if time.monotonic() > deadline:
                raise RuntimeError('Capture time budget exhausted')
            if not 0 < amount <= 0x20000:
                raise RuntimeError('Unbounded read')
            data, got = C.create_string_buffer(amount), C.c_size_t()
            if not k.ReadProcessMemory(handle, address, data, amount, C.byref(got)) or got.value != amount:
                raise C.WinError(C.get_last_error())
            return data.raw

        samples, errors = [], []
        deadline = time.monotonic() + seconds
        started = time.monotonic()
        while time.monotonic() < deadline and len(samples) < sample_limit:
            try:
                item = sample(read, base)
                if item['records'] or item['queries']:
                    item['elapsed_ms'] = round((time.monotonic() - started) * 1000)
                    samples.append(item)
            except (OSError, RuntimeError) as error:
                if len(errors) < 20:
                    errors.append(str(error))
            time.sleep(min(interval_ms / 1000, max(0, deadline - time.monotonic())))
        return {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'pid': pid, 'exe_sha256': EXPECTED, 'dll_sha256': hashlib.sha256(EXE.with_name('hid.dll').read_bytes()).hexdigest(),
                'process_access': 'QUERY_LIMITED_INFORMATION | VM_READ only',
                'observer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'requested_sample_limit': sample_limit, 'interval_ms': interval_ms,
                'ctrl_state': 'Not read automatically; operator supplies requested ON/OFF state in capture label.',
                'samples': samples, 'errors': errors, 'writes': 0}
    finally:
        k.CloseHandle(handle)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pid', type=int)
    parser.add_argument('--label', required=True)
    parser.add_argument('--seconds', type=int, default=8, choices=range(1, 11), metavar='1..10')
    parser.add_argument('--samples', type=int, default=6, choices=range(1, 33), metavar='1..32')
    parser.add_argument('--interval-ms', type=int, default=40, choices=range(40, 1001), metavar='40..1000')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,48}', args.label):
        parser.error('Invalid label')
    report = capture(args.pid, args.seconds, args.samples, args.interval_ms)
    report['label'] = args.label
    folder = ROOT / 'work/live-lights-readonly'
    folder.mkdir(exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    path = folder / f'{stamp}-{args.label}.json'
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'path': str(path), 'samples': len(report['samples']),
                      'record_counts': [s['pass67_record_count'] for s in report['samples']],
                      'query_counts': [len(s['queries']) for s in report['samples']],
                      'errors': report['errors'][:3], 'writes': 0}, indent=2))


if __name__ == '__main__':
    main()
