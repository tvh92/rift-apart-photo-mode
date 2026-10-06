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

DLL_HASH = '16dcd44057c3114b123e25974b9b563afc487650686d3985784614caba5f7cbd'
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


def registered_light_queries(read, base, view, diagnostics=None):
    """Typed query request slots, not a guessed world-LightDef catalog.

    107B760 copies the LightSubmit builder's output-array/count pointers into
    the C0-byte slot. 12B8740 consumes those exact fields. Validate both the
    callback/manager and the derived query's view and output fields.
    """
    results, errors = [], []
    visited = set()
    for registry in (0x6414C30, 0x64151D8):
        header = read(base + registry + 0x508, 16)
        backing, capacity, count = struct.unpack('<Qii', header)
        generation = read(base + registry + 0x598, 4)
        stats = {'registry_rva': hex(registry), 'count': count, 'capacity': capacity,
                 'callback_matches': 0, 'manager_matches': 0, 'query_owner_candidates': []}
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
            chunks.append((address, read(address, n * 0xC0)))
        for address, data in chunks:
            for offset in range(0, len(data), 0xC0):
                slot = data[offset:offset + 0xC0]
                if struct.unpack_from('<Q', slot, 0x78)[0] != base + 0x12B8740:
                    continue
                stats['callback_matches'] += 1
                if struct.unpack_from('<Q', slot, 0x38)[0] != base + 0x674EC10:
                    continue
                stats['manager_matches'] += 1
                output, counter = (struct.unpack_from('<Q', slot, off)[0] for off in (0x68, 0x70))
                # Fixed request writes query+10; optional request writes+20.
                for count_offset, array_offset in ((0x10, 8), (0x20, 0x18)):
                    query = counter - count_offset
                    try:
                        pointer(query)
                        head = read(query, 0x28)
                        if len(stats['query_owner_candidates']) < 12:
                            stats['query_owner_candidates'].append({
                                'query': hex(query), 'owner': hex(struct.unpack_from('<Q', head)[0]),
                                'count_offset': hex(count_offset),
                                'request_output': hex(output),
                                'query_output': hex(struct.unpack_from('<Q', head, array_offset)[0]),
                                'query_header_hex': head.hex(),
                                'request_slot': hex(address + offset),
                                'request_generation_hex': generation.hex(),
                                'output_field_matches': struct.unpack_from('<Q', head, array_offset)[0] == output,
                            })
                        if (struct.unpack_from('<Q', head)[0] != view or
                                struct.unpack_from('<Q', head, array_offset)[0] != output):
                            continue
                        if query in visited:
                            break
                        result = query_summary(read, query, view)
                        if read(address + offset, 0xC0) != slot:
                            raise RuntimeError('Light query request changed during sample')
                        result['request_registry_rva'] = hex(registry)
                        result['request_slot'] = hex(address + offset)
                        results.append(result)
                        visited.add(query)
                        break
                    except (OSError, RuntimeError) as error:
                        if len(errors) < 12:
                            errors.append(str(error))
        # Request slots are immutable while active apart from work state.
        # Recheck ownership/generation; per-slot matching guards typed queries.
        if (read(base + registry + 0x508, 16) != header or
                read(base + registry + 0x598, 4) != generation):
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
    request_diagnostics = []
    queries, request_errors = registered_light_queries(read, base, view, request_diagnostics)
    for p, data in segment_data:
        if read(p, len(data)) != data:
            raise RuntimeError('Submission queue changed during sample')
    if (read(view + QUEUE, 16) != header or read(base + ARCHIVE, 16) != archived or
            (arch_count and read(arch_ptr, len(descriptors)) != descriptors) or
            read(base + PRIMARY, 8) != view_word or read(view + 0x30, 12) != position or
            read(base + PHOTO, 0x58) != photo):
        raise RuntimeError('Photo/view/queue ownership changed during sample')
    return {'view': hex(view), 'position_30': floats(position, 0, 3),
            'queue_identity': identity, 'segments': len(segments),
            'pass67_record_count': len(records), 'records': records,
            'queries': queries, 'errors': errors,
            'request_errors': request_errors,
            'request_diagnostics': request_diagnostics,
            'query_limit': 'Typed request registry only; source/query fields are non-atomic. Empty passBB marker is not used.',
            'atomic': False, 'callback_order_proven': False,
            'limit': 'Transient CPU submissions only; queue order is not final callback order. Absence or >512 does not establish the cause of lost illumination.'}


def capture(pid, seconds):
    if hashlib.sha256(EXE.read_bytes()).hexdigest() != EXPECTED:
        raise RuntimeError('Unsupported executable')
    if hashlib.sha256(EXE.with_name('hid.dll').read_bytes()).hexdigest() != DLL_HASH:
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
        while time.monotonic() < deadline and len(samples) < 6:
            try:
                item = sample(read, base)
                if item['records'] or item['queries']:
                    samples.append(item)
            except (OSError, RuntimeError) as error:
                if len(errors) < 20:
                    errors.append(str(error))
            time.sleep(0.04)
        return {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'pid': pid, 'exe_sha256': EXPECTED, 'dll_sha256': DLL_HASH,
                'process_access': 'QUERY_LIMITED_INFORMATION | VM_READ only',
                'ctrl_state': 'Not read automatically; operator supplies requested ON/OFF state in capture label.',
                'samples': samples, 'errors': errors, 'writes': 0}
    finally:
        k.CloseHandle(handle)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pid', type=int)
    parser.add_argument('--label', required=True)
    parser.add_argument('--seconds', type=int, default=8, choices=range(1, 11))
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,48}', args.label):
        parser.error('Invalid label')
    report = capture(args.pid, args.seconds)
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
