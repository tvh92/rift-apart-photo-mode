"""Read specific light source prefixes captured earlier; no process writes.

Checks whether a source object that dropped out of the primary query input
still exists unchanged. Compares the current 0xD0-byte prefix with the
reference raw_hex from an earlier capture JSON. Exact EXE/DLL guards and
QUERY_LIMITED_INFORMATION|VM_READ access only.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
from pathlib import Path
import struct
from capture_live_atmosphere import EXE, EXPECTED
from capture_photo_lights_readonly import DLL_HASH, pointer, source_summary


def compare(reference, current):
    changed = [hex(o) for o in range(0, 0xD0, 4) if reference[o:o + 4] != current[o:o + 4]]
    return {'identical': not changed, 'changed_dwords': changed,
            'dword_60': [struct.unpack_from('<I', reference, 0x60)[0], struct.unpack_from('<I', current, 0x60)[0]],
            'current': {k: v for k, v in source_summary(current).items() if k != 'raw_hex'}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pid', type=int)
    parser.add_argument('reference', type=Path)
    parser.add_argument('sources', nargs='+')
    args = parser.parse_args()
    if hashlib.sha256(EXE.read_bytes()).hexdigest() != EXPECTED:
        raise SystemExit('Unsupported executable')
    if hashlib.sha256(EXE.with_name('hid.dll').read_bytes()).hexdigest() != DLL_HASH:
        raise SystemExit('Unexpected mod DLL')
    ref = json.loads(args.reference.read_text())
    known = {}
    for s in ref['samples']:
        for q in s['queries']:
            known.update(q['sources'])
    k = C.WinDLL('kernel32', use_last_error=True)
    k.OpenProcess.argtypes, k.OpenProcess.restype = [W.DWORD, W.BOOL, W.DWORD], W.HANDLE
    k.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD)]
    k.ReadProcessMemory.argtypes = [W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)]
    k.CloseHandle.argtypes = [W.HANDLE]
    handle = k.OpenProcess(0x1010, False, args.pid)
    if not handle:
        raise C.WinError(C.get_last_error())
    try:
        name, size = C.create_unicode_buffer(32768), W.DWORD(32768)
        if not k.QueryFullProcessImageNameW(handle, 0, name, C.byref(size)):
            raise C.WinError(C.get_last_error())
        if Path(name.value).resolve() != EXE.resolve():
            raise SystemExit('Unexpected process path')
        report = {}
        for text in args.sources:
            address = pointer(int(text, 16))
            if text not in known or 'raw_hex' not in known[text]:
                report[text] = {'error': 'No reference prefix in capture'}
                continue
            data, got = C.create_string_buffer(0xD0), C.c_size_t()
            if not k.ReadProcessMemory(handle, address, data, 0xD0, C.byref(got)) or got.value != 0xD0:
                report[text] = {'error': 'Unreadable (possibly freed)'}
                continue
            report[text] = compare(bytes.fromhex(known[text]['raw_hex']), data.raw)
        print(json.dumps({'writes': 0, 'sources': report}, indent=2))
    finally:
        k.CloseHandle(handle)


if __name__ == '__main__':
    main()
