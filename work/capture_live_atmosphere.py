"""Capture only the proven current atmosphere block; never write game memory.

Usage: python work/capture_live_atmosphere.py PID --label near
       python work/capture_live_atmosphere.py PID --label far
Exact executable guard, read-only process access, no heap scan or injection.
Offsets here identify known object/resource locations, not named scalar controls.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import datetime
import hashlib
import json
from pathlib import Path
import re
import struct
import time

EXE = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\RiftApart.exe')
EXPECTED = '51299faca61866cf10ea9035a15b8f22600a56557dd5ffc1aad390d5a54e6d82'
ROOT = Path(__file__).resolve().parents[1]
REGISTRY_RVA = 0x52DDA20
FALLBACK_RVA = 0x6240400
BLOCK_SIZE = 0x6A0


class Module(C.Structure):
    _fields_ = [('dwSize', W.DWORD), ('th32ModuleID', W.DWORD),
                ('th32ProcessID', W.DWORD), ('GlblcntUsage', W.DWORD),
                ('ProccntUsage', W.DWORD), ('modBaseAddr', C.c_void_p),
                ('modBaseSize', W.DWORD), ('hModule', W.HMODULE),
                ('szModule', W.WCHAR * 256), ('szExePath', W.WCHAR * 260)]


def capture(pid):
    k = C.WinDLL('kernel32', use_last_error=True)
    k.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
    k.OpenProcess.restype = W.HANDLE
    k.CloseHandle.argtypes = [W.HANDLE]
    k.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD)]
    k.ReadProcessMemory.argtypes = [W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)]
    k.ReadProcessMemory.restype = W.BOOL
    k.CreateToolhelp32Snapshot.argtypes = [W.DWORD, W.DWORD]
    k.CreateToolhelp32Snapshot.restype = W.HANDLE
    k.Module32FirstW.argtypes = [W.HANDLE, C.POINTER(Module)]
    k.Module32NextW.argtypes = [W.HANDLE, C.POINTER(Module)]
    handle = k.OpenProcess(0x1010, False, pid)  # QUERY_LIMITED_INFORMATION | VM_READ
    if not handle:
        raise C.WinError(C.get_last_error())
    try:
        name = C.create_unicode_buffer(32768)
        size = W.DWORD(len(name))
        if not k.QueryFullProcessImageNameW(handle, 0, name, C.byref(size)):
            raise C.WinError(C.get_last_error())
        if Path(name.value).resolve() != EXE.resolve():
            raise RuntimeError('Refusing unexpected executable path')
        if hashlib.sha256(EXE.read_bytes()).hexdigest() != EXPECTED:
            raise RuntimeError('Refusing unsupported executable build')
        snap = k.CreateToolhelp32Snapshot(0x18, pid)
        if snap == C.c_void_p(-1).value:
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
            buffer = C.create_string_buffer(amount)
            got = C.c_size_t()
            if not k.ReadProcessMemory(handle, address, buffer, amount, C.byref(got)) or got.value != amount:
                raise C.WinError(C.get_last_error())
            return buffer.raw

        pointer_address = base + REGISTRY_RVA + 0x1C8
        for _ in range(3):
            before = read(pointer_address, 8)
            pointer = struct.unpack('<Q', before)[0]
            selected = pointer or base + FALLBACK_RVA
            data = read(selected, BLOCK_SIZE)
            after = read(pointer_address, 8)
            if before == after:
                break
        else:
            raise RuntimeError('Current atmosphere changed during capture; retry')
        # Live values can change while reading. Pointer stability does not imply
        # an atomic snapshot of every field, so compare repeat captures as needed.
        report = {
            'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'pid': pid, 'process': str(EXE), 'exe_sha256': EXPECTED,
            'module_base': hex(base), 'registry_rva': hex(REGISTRY_RVA),
            'selected_pointer': hex(selected), 'fallback': not bool(pointer),
            'size': BLOCK_SIZE, 'pointer_stable': True,
            'atomic_fields': False, 'block_sha256': hashlib.sha256(data).hexdigest(),
            'fog_map_reference_blocks': {
                hex(offset): data[offset:offset + 0x18].hex() for offset in (0x478, 0x490)
            },
            'semantics': 'Named fog-map references only; scalar field names remain unproven.',
        }
        # FB1130 accepts slots0..3; out-of-range indices fall back to slot0.
        # The renderer caller uses view+F90, so capture every valid slot too.
        report['registry_slots'] = {}
        for index in range(4):
            try:
                slot_address = base + REGISTRY_RVA + 0x1C8 + index * 8
                slot_before = read(slot_address, 8)
                slot_pointer = struct.unpack('<Q', slot_before)[0]
                slot_data = read(slot_pointer or base + FALLBACK_RVA, BLOCK_SIZE)
                if read(slot_address, 8) != slot_before:
                    raise RuntimeError('Slot pointer changed during capture')
                report['registry_slots'][str(index)] = {
                    'pointer': hex(slot_pointer), 'fallback': not bool(slot_pointer),
                    'sha256': hashlib.sha256(slot_data).hexdigest(),
                    'block_hex': slot_data.hex(),
                }
            except (OSError, RuntimeError) as error:
                report['registry_slots'][str(index)] = {'error': str(error)}
        try:
            view_before = read(base + 0x6732C40, 8)
            view = struct.unpack('<Q', view_before)[0]
            for _ in range(100):
                if view:
                    break
                time.sleep(0.001)
                view_before = read(base + 0x6732C40, 8)
                view = struct.unpack('<Q', view_before)[0]
            view_index = struct.unpack('<i', read(view + 0xF90, 4))[0] if view else None
            report['current_render_view_candidate'] = {
                'pointer': hex(view), 'atmosphere_index': view_index,
                'pointer_stable': read(base + 0x6732C40, 8) == view_before,
                'limit': 'Current renderer global; selected subview/explicit atmosphere override may differ.',
            }
            if view:
                report['current_render_view_candidate']['prefix_440_hex'] = read(view, 0x440).hex()
                report['current_render_view_candidate']['tail_F80_2040_hex'] = read(view + 0xF80, 0x10C0).hex()
        except OSError as error:
            report['current_render_view_candidate'] = {'error': str(error)}
        report['postprocess_default_global_5339340'] = read(base + 0x5339340, 1).hex()
        # Named FogInit callback FB4EC0 consumes these two renderer globals.
        # They are transient; bound retries and require both pointers to remain
        # stable during a read. This does not suspend threads or make it atomic.
        renderer_samples = []
        for _ in range(500):
            try:
                pair = read(base + 0x6732C40, 16)
                render_view, render_block = struct.unpack('<QQ', pair)
                if render_view and render_block:
                    render_data = read(render_block, 0x760)
                    view_position = read(render_view + 0x30, 12)
                    if read(base + 0x6732C40, 16) == pair:
                        renderer_samples.append({
                            'view': hex(render_view), 'block': hex(render_block),
                            'main_view_global': hex(struct.unpack('<Q', read(base + 0x6739B10, 8))[0]),
                            'atmosphere_index': struct.unpack('<i', read(render_view + 0xF90, 4))[0],
                            'view_position_30_raw_floats': struct.unpack('<3f', view_position),
                            'block_hex': render_data.hex(),
                            'sha256': hashlib.sha256(render_data).hexdigest(),
                            'fog_110_19C_hex': render_data[0x110:0x19C].hex(),
                        })
                        if len(renderer_samples) >= 3:
                            break
            except OSError:
                pass  # Another rendering job can retire a transient block.
            time.sleep(0.001)
        report['renderer_samples'] = renderer_samples
        report['fog_blend_globals_raw'] = {
            hex(address): read(base + address, 4).hex()
            for address in (0x53393B0, 0x53393B4)
        }
        report['primary_view_candidates'] = {}
        for address in (0x6739B08, 0x6739B10):
            ptr = struct.unpack('<Q', read(base + address, 8))[0]
            report['primary_view_candidates'][hex(address)] = {'pointer':hex(ptr)}
            if ptr:
                report['primary_view_candidates'][hex(address)].update({
                    'position_30_raw_floats':struct.unpack('<3f',read(ptr+0x30,12)),
                    'index_F90':struct.unpack('<i',read(ptr+0xF90,4))[0],
                })
        report['render_settings_callback'] = hex(struct.unpack('<Q',read(base+0x65A3080,8))[0])
        report['prepared_fog_context_69C_724_hex'] = read(base+0x67326D0+0x69C,0x88).hex()
        photo = read(base+0x6138200,0x58)
        report['photo_system_candidate'] = {
            'pointer':hex(base+0x6138200),
            'vtable_rva':hex(struct.unpack_from('<Q',photo)[0]-base),
            'state_50':struct.unpack_from('<i',photo,0x50)[0],
            'setup_54':photo[0x54],
        }
        return report, data
    finally:
        k.CloseHandle(handle)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pid', type=int)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,48}', args.label):
        parser.error('Label must contain 1-48 letters, digits, underscores or hyphens')
    report, data = capture(args.pid)
    directory = ROOT / 'work/live-atmosphere-readonly'
    directory.mkdir(exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    stem = directory / f'{stamp}-{args.label}'
    stem.with_suffix('.bin').write_bytes(data)
    report['label'] = args.label
    report['binary'] = str(stem.with_suffix('.bin'))
    stem.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    # Keep raw block bytes in the saved evidence, out of the console.
    summary = dict(report)
    summary['registry_slots'] = {key: {n:v for n,v in value.items() if n != 'block_hex'}
                                 for key,value in report['registry_slots'].items()}
    summary['current_render_view_candidate'] = {
        n:v for n,v in report['current_render_view_candidate'].items() if not n.endswith('_hex')
    }
    summary['renderer_samples'] = [{n:v for n,v in value.items() if not n.endswith('_hex')}
                                   for value in report['renderer_samples']]
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
