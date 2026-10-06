"""Locate light records in manager 0x674EC10's cell/block lists; no writes.

Layout from light-request-worker-traversal.md: mgr+00 record base, +30 cell
array (0x30 stride, +48 = count-1), +50 block pool (0x100 stride, +60 count).
Cell: +00 centre, +10 half-extents, +20 first block, +24 element count,
+2B bit 0x40 enabled. Block: +00 next index, +0A int16 entry count,
entries at +10 stride 0x10: +4 u32 record index (4-byte units), +8 int16
x,y,z,r scaled by 0.5. Output record pointer = base + index*4.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
from pathlib import Path
import struct
from capture_live_atmosphere import Module, EXE, EXPECTED
from capture_photo_lights_readonly import DLL_HASHES, pointer

MGR = 0x674EC10
MAX_CELLS = 1 << 16
MAX_BLOCKS = 1 << 18


def read_chunked(read, address, size):
    parts = []
    for offset in range(0, size, 0x20000):
        parts.append(read(address + offset, min(0x20000, size - offset)))
    return b''.join(parts)


def scan(read, base, targets):
    head = read(base + MGR, 0x68)
    records = struct.unpack_from('<Q', head, 0)[0]
    cells_ptr = struct.unpack_from('<Q', head, 0x30)[0]
    cell_count = struct.unpack_from('<i', head, 0x48)[0] + 1
    blocks_ptr = struct.unpack_from('<Q', head, 0x50)[0]
    block_count = struct.unpack_from('<i', head, 0x60)[0]
    if not (0 < cell_count <= MAX_CELLS and 0 < block_count <= MAX_BLOCKS):
        raise RuntimeError(f'Manager counts rejected: cells={cell_count} blocks={block_count}')
    cells = read_chunked(read, pointer(cells_ptr), cell_count * 0x30)
    blocks = read_chunked(read, pointer(blocks_ptr), block_count * 0x100)
    wanted = {}
    for target in targets:
        delta = target - records
        if delta < 0 or delta % 4:
            raise RuntimeError(f'Record {hex(target)} not in manager record space')
        wanted[delta // 4] = hex(target)
    found = {t: [] for t in wanted.values()}
    visited = set()
    for index in range(cell_count):
        cell = cells[index * 0x30:(index + 1) * 0x30]
        block, count = struct.unpack_from('<ii', cell, 0x20)
        steps = 0
        while 0 <= block < block_count and steps < 4096:
            visited.add(block)
            data = blocks[block * 0x100:(block + 1) * 0x100]
            entries = struct.unpack_from('<h', data, 0x0A)[0]
            for e in range(max(0, min(entries, 15))):
                entry = data[0x10 + e * 0x10:0x20 + e * 0x10]
                rec = struct.unpack_from('<I', entry, 4)[0]
                if rec in wanted:
                    sphere = [v * 0.5 for v in struct.unpack_from('<4h', entry, 8)]
                    found[wanted[rec]].append({
                        'cell': index, 'block': block, 'entry': e, 'key': struct.unpack_from('<H', entry)[0],
                        'sphere_xyzr': sphere,
                        'cell_centre': struct.unpack_from('<3f', cell, 0),
                        'cell_half': struct.unpack_from('<3f', cell, 0x10),
                        'cell_count': count, 'cell_flags_28_2F': cell[0x28:0x30].hex(),
                        'cell_enabled': bool(cell[0x2B] & 0x40)})
            block = struct.unpack_from('<i', data, 0)[0]
            steps += 1
    if read(base + MGR, 0x68) != head:
        raise RuntimeError('Manager header changed during scan')
    enabled = sum(1 for i in range(cell_count) if cells[i * 0x30 + 0x2B] & 0x40)
    return {'records_base': hex(records), 'cells': cell_count, 'enabled_cells': enabled,
            'blocks': block_count, 'blocks_reached': len(visited), 'found': found,
            'atomic': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pid', type=int)
    parser.add_argument('records', nargs='+')
    args = parser.parse_args()
    if hashlib.sha256(EXE.read_bytes()).hexdigest() != EXPECTED:
        raise SystemExit('Unsupported executable')
    if hashlib.sha256(EXE.with_name('hid.dll').read_bytes()).hexdigest() not in DLL_HASHES:
        raise SystemExit('Unexpected mod DLL')
    k = C.WinDLL('kernel32', use_last_error=True)
    k.OpenProcess.argtypes, k.OpenProcess.restype = [W.DWORD, W.BOOL, W.DWORD], W.HANDLE
    k.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD)]
    k.ReadProcessMemory.argtypes = [W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)]
    k.CloseHandle.argtypes = [W.HANDLE]
    k.CreateToolhelp32Snapshot.argtypes, k.CreateToolhelp32Snapshot.restype = [W.DWORD, W.DWORD], W.HANDLE
    k.Module32FirstW.argtypes = [W.HANDLE, C.POINTER(Module)]
    k.Module32NextW.argtypes = [W.HANDLE, C.POINTER(Module)]
    handle = k.OpenProcess(0x1010, False, args.pid)
    if not handle:
        raise C.WinError(C.get_last_error())
    try:
        name, size = C.create_unicode_buffer(32768), W.DWORD(32768)
        if not k.QueryFullProcessImageNameW(handle, 0, name, C.byref(size)):
            raise C.WinError(C.get_last_error())
        if Path(name.value).resolve() != EXE.resolve():
            raise SystemExit('Unexpected process path')
        snap = k.CreateToolhelp32Snapshot(0x18, args.pid)
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
            raise SystemExit('Executable module not found')

        def read(address, amount):
            if not 0 < amount <= 0x20000:
                raise RuntimeError('Unbounded read')
            data, got = C.create_string_buffer(amount), C.c_size_t()
            if not k.ReadProcessMemory(handle, address, data, amount, C.byref(got)) or got.value != amount:
                raise C.WinError(C.get_last_error())
            return data.raw

        report = scan(read, base, [pointer(int(t, 16)) for t in args.records])
        report['writes'] = 0
        print(json.dumps(report, indent=2))
    finally:
        k.CloseHandle(handle)


if __name__ == '__main__':
    main()
