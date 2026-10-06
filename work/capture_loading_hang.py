"""Diagnostic thread-context snapshot and bounded stack reads, no code writes.

Uses Windows process snapshots; never manually suspend/resume any game thread.
The stack candidates are raw addresses, not claimed unwound call stacks.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import datetime
import hashlib
import json
from pathlib import Path
import struct
from capture_live_atmosphere import EXE, EXPECTED, Module, ROOT


class ThreadEntry(C.Structure):
    _fields_ = [('exit', W.DWORD), ('teb', C.c_void_p), ('pid', W.DWORD),
                ('tid', W.DWORD), ('affinity', C.c_size_t), ('priority', C.c_int),
                ('base_priority', C.c_int), ('syscall_arg', C.c_void_p),
                ('syscall', W.WORD), ('create_time', W.FILETIME),
                ('exit_time', W.FILETIME), ('kernel_time', W.FILETIME),
                ('user_time', W.FILETIME), ('start', C.c_void_p),
                ('capture_time', W.FILETIME), ('flags', W.DWORD),
                ('suspend_count', W.WORD), ('context_size', W.WORD),
                ('context', C.c_void_p)]


class Lock(C.Structure):
    _fields_ = [('name', W.WCHAR * 128), ('timeout', C.c_int64), ('alertable', W.BOOL)]


class WaitThread(C.Structure):
    _fields_ = [('pid', W.DWORD), ('tid', W.DWORD), ('wait_ms', W.DWORD), ('switches', W.DWORD)]


class WaitObject(C.Union):
    _fields_ = [('lock', Lock), ('thread', WaitThread)]


class WaitNode(C.Structure):
    _fields_ = [('type', C.c_int), ('status', C.c_int), ('object', WaitObject)]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('pid', type=int)
    a = p.parse_args()
    k = C.WinDLL('kernel32', use_last_error=True)
    k.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]; k.OpenProcess.restype = W.HANDLE
    k.CloseHandle.argtypes = [W.HANDLE]
    k.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD)]
    k.ReadProcessMemory.argtypes = [W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)]
    k.CreateToolhelp32Snapshot.argtypes = [W.DWORD, W.DWORD]; k.CreateToolhelp32Snapshot.restype = W.HANDLE
    k.Module32FirstW.argtypes = [W.HANDLE, C.POINTER(Module)]
    k.Module32NextW.argtypes = [W.HANDLE, C.POINTER(Module)]
    k.PssCaptureSnapshot.argtypes = [W.HANDLE, W.DWORD, W.DWORD, C.POINTER(W.HANDLE)]
    k.PssCaptureSnapshot.restype = W.DWORD
    k.PssFreeSnapshot.argtypes = [W.HANDLE, W.HANDLE]
    k.PssWalkMarkerCreate.argtypes = [C.c_void_p, C.POINTER(W.HANDLE)]
    k.PssWalkMarkerFree.argtypes = [W.HANDLE]
    k.PssWalkSnapshot.argtypes = [W.HANDLE, W.DWORD, W.HANDLE, C.c_void_p, W.DWORD]
    k.PssWalkSnapshot.restype = W.DWORD
    handle = k.OpenProcess(0x410, False, a.pid)  # Query + VM_READ, no write access
    if not handle: raise C.WinError(C.get_last_error())
    try:
        path = C.create_unicode_buffer(32768); length = W.DWORD(len(path))
        if not k.QueryFullProcessImageNameW(handle, 0, path, C.byref(length)): raise C.WinError(C.get_last_error())
        if Path(path.value).resolve() != EXE.resolve(): raise RuntimeError('Unexpected process path')
        if hashlib.sha256(EXE.read_bytes()).hexdigest() != EXPECTED: raise RuntimeError('Unsupported EXE')
        modules = []
        snap = k.CreateToolhelp32Snapshot(0x18, a.pid)
        if snap == C.c_void_p(-1).value: raise C.WinError(C.get_last_error())
        try:
            m = Module(); m.dwSize = C.sizeof(m)
            ok = k.Module32FirstW(snap, C.byref(m))
            while ok:
                modules.append({'name': m.szModule, 'base': m.modBaseAddr, 'size': m.modBaseSize, 'path': m.szExePath})
                ok = k.Module32NextW(snap, C.byref(m))
        finally: k.CloseHandle(snap)

        def address(value):
            if not value: return None
            for m in modules:
                if m['base'] <= value < m['base'] + m['size']:
                    return f"{m['name']}+0x{value-m['base']:x}"
            return hex(value)

        def small_read(pointer, amount):
            buffer = C.create_string_buffer(amount); got = C.c_size_t()
            if not k.ReadProcessMemory(handle, pointer, buffer, amount, C.byref(got)) or got.value != amount:
                return None
            return buffer.raw

        native_state = {}
        game_base = next(m['base'] for m in modules if m['name'].lower() == 'riftapart.exe')
        renderer = small_read(game_base + 0x6745B20, 0x5D0)
        if renderer:
            index = renderer[0x5C8]
            native_state['renderer_index'] = index
            if index < 2:
                renderer_object = struct.unpack_from('<Q', renderer, index * 8)[0]
                header = small_read(renderer_object, 8)
                if header:
                    vt = struct.unpack('<Q', header)[0]
                    slots = small_read(vt, 0xF0)
                    native_state['renderer_object'] = hex(renderer_object)
                    native_state['renderer_vtable'] = address(vt)
                    if slots:
                        native_state['renderer_wait_slot_E8'] = address(struct.unpack_from('<Q', slots, 0xE8)[0])
                        native_state['renderer_submit_slot_E0'] = address(struct.unpack_from('<Q', slots, 0xE0)[0])
        for rva in [0x6734820, 0x67356E0, 0x67356E8, 0x6732D3C]:
            value = small_read(game_base+rva,4)
            if value: native_state[hex(rva)] = struct.unpack('<I', value)[0]
        proxy = next(m for m in modules if m['name'].lower() == 'hid.dll' and Path(m['path']).parent == EXE.parent)
        for rva in [0x2F000,0x2F008,0x2F024,0x2F1D0,0x2F224]:
            value = small_read(proxy['base']+rva,4)
            if value: native_state['proxy_'+hex(rva)] = struct.unpack('<I',value)[0]
        value = small_read(game_base+0x6794FE0,8)
        if value: native_state['native_frame_time'] = struct.unpack('<d',value)[0]

        pss = W.HANDLE(); marker = W.HANDLE(); threads = []
        result = k.PssCaptureSnapshot(handle, 0x180, 0x100007, C.byref(pss))
        if result: raise C.WinError(result)
        try:
            result = k.PssWalkMarkerCreate(None, C.byref(marker))
            if result: raise C.WinError(result)
            try:
                while True:
                    t = ThreadEntry()
                    result = k.PssWalkSnapshot(pss, 3, marker, C.byref(t), C.sizeof(t))
                    if result == 259: break
                    if result: raise C.WinError(result)
                    row = {'tid': t.tid, 'start': address(t.start), 'suspend_count': t.suspend_count,
                           'syscall': t.syscall, 'context_size': t.context_size,
                           'kernel_time': t.kernel_time.dwLowDateTime + (t.kernel_time.dwHighDateTime << 32),
                           'user_time': t.user_time.dwLowDateTime + (t.user_time.dwHighDateTime << 32)}
                    if t.context and t.context_size >= 256:
                        context = C.string_at(t.context, t.context_size)
                        registers = dict(zip(['rax','rcx','rdx','rbx','rsp','rbp','rsi','rdi','r8','r9','r10','r11','r12','r13','r14','r15','rip'], struct.unpack_from('<17Q', context, 120)))
                        row['registers'] = {n: hex(v) for n,v in registers.items()}
                        row['instruction'] = address(registers['rip'])
                        buf = C.create_string_buffer(8192); got = C.c_size_t()
                        k.ReadProcessMemory(handle, registers['rsp'], buf, len(buf), C.byref(got))
                        if not got.value:
                            # A short stack near its top cannot span an entire
                            # 8 KiB read. Capture the remainder of its page.
                            amount = 0x1000 - (registers['rsp'] & 0xFFF)
                            k.ReadProcessMemory(handle, registers['rsp'], buf, amount, C.byref(got))
                        stack = buf.raw[:got.value]
                        row['stack_hex'] = stack.hex()
                        row['stack_address_candidates'] = [
                            {'offset': hex(i), 'address': address(v)}
                            for i in range(0, len(stack)-7, 8)
                            for v in [struct.unpack_from('<Q', stack, i)[0]]
                            if any(m['base'] <= v < m['base']+m['size'] for m in modules)
                        ]
                    threads.append(row)
            finally: k.PssWalkMarkerFree(marker)
        finally: k.PssFreeSnapshot(handle, pss)

        adv = C.WinDLL('advapi32', use_last_error=True)
        adv.OpenThreadWaitChainSession.argtypes = [W.DWORD, C.c_void_p]; adv.OpenThreadWaitChainSession.restype = W.HANDLE
        adv.CloseThreadWaitChainSession.argtypes = [W.HANDLE]
        adv.GetThreadWaitChain.argtypes = [W.HANDLE, C.c_size_t, W.DWORD, W.DWORD, C.POINTER(W.DWORD), C.POINTER(WaitNode), C.POINTER(W.BOOL)]
        session = adv.OpenThreadWaitChainSession(0, None)
        if session:
            try:
                for row in threads:
                    nodes = (WaitNode * 16)(); count = W.DWORD(16); cycle = W.BOOL()
                    if adv.GetThreadWaitChain(session, 0, 0, row['tid'], C.byref(count), nodes, C.byref(cycle)):
                        row['wait_cycle'] = bool(cycle.value)
                        row['wait_chain'] = [
                            {'type': n.type, 'status': n.status, **(
                                {'pid': n.object.thread.pid, 'tid': n.object.thread.tid, 'wait_ms': n.object.thread.wait_ms}
                                if n.type == 8 else {'name': n.object.lock.name})}
                            for n in nodes[:min(count.value,16)]
                        ]
                    else: row['wait_chain_error'] = C.get_last_error()
            finally: adv.CloseThreadWaitChainSession(session)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        output = ROOT / f'work/loading-hang-{stamp}.json'
        output.write_text(json.dumps({'pid':a.pid,'exe_sha256':EXPECTED,'native_state':native_state,'modules':modules,'threads':threads,'warning':'Raw stack addresses are candidates, not unwound frames.'},indent=2)+'\n',encoding='utf-8')
        print('Saved', output, 'threads', len(threads))
        print(json.dumps(native_state,indent=2))
        for row in threads:
            if row.get('wait_cycle') or row['suspend_count'] or any('hid.dll+' in x['address'] for x in row.get('stack_address_candidates',[])):
                print(json.dumps({n:v for n,v in row.items() if n not in ['stack_hex','registers']},indent=2))
    finally: k.CloseHandle(handle)


if __name__ == '__main__': main()
