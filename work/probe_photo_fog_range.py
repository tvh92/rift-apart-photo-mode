"""Bounded Photo-only atmosphere fog experiment.

Dry-run by default. --apply changes one endpoint float, or with --near-fog
the captured numeric fog block, for at most 180 seconds, then restores owned values.
No files in the game directory, callbacks, executable bytes, or saves change.
Run only for a coordinated visual comparison; never leave this probe running.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import datetime
import hashlib
import json
import math
from pathlib import Path
import struct
import time
from capture_live_atmosphere import capture, EXE, EXPECTED, BLOCK_SIZE, REGISTRY_RVA, ROOT

PHOTO_RVA = 0x6138200
PHOTO_VTABLE = 0x2FBF630
ENDPOINT_OFFSET = 0x450
DLL_HASH = '5c36943c6dfb45713382bf471e6f9939f857ee94f7789b8fefb2fc3abc292842'


def valid_photo(data, base):
    return (len(data) == 0x58 and struct.unpack_from('<Q', data)[0] == base + PHOTO_VTABLE
            and struct.unpack_from('<i', data, 0x50)[0] == 4 and data[0x54] == 1)


def restoration_action(current_pointer, expected_pointer, header, expected_header, value, original, replacement):
    if current_pointer != expected_pointer or header != expected_header:
        return 'object_changed'
    if value == original:
        return 'already_original'
    if value != replacement:
        return 'native_value_changed'
    return 'restore'


def near_fog_payload(capture_report):
    """Copy numeric fog only, excluding the two texture-dependent tail fields."""
    if capture_report['exe_sha256'] != EXPECTED or capture_report.get('label') != 'corson-near-processed':
        raise RuntimeError('Refusing unrelated near-fog evidence')
    photo=capture_report['photo_system_candidate']
    if (photo['vtable_rva'],photo['state_50'],photo['setup_54']) != ('0x2fbf630',4,1):
        raise RuntimeError('Near capture was not ordinary Photo mode')
    raw=bytes.fromhex(capture_report['renderer_samples'][-1]['fog_110_19C_hex'])[:0x84]
    if len(raw)!=0x84:
        raise RuntimeError('Incomplete processed fog capture')
    floats=struct.unpack('<33f',raw)
    if not all(math.isfinite(value) for value in floats):
        raise RuntimeError('Nonfinite fog settings')
    if not (all(0<=value<=16 for value in floats[:3]) and 0<=floats[0x54//4]<=1
            and 0<=floats[0x60//4]<floats[0x64//4]<=512):
        raise RuntimeError('Unexpected fog colour, opacity, or endpoints')
    return raw


def restore_owned_fields(value,original,replacement):
    if not len(value)==len(original)==len(replacement) or len(value)%4:
        raise RuntimeError('Invalid restoration block')
    merged=bytearray(value)
    preserved=[]
    for offset in range(0,len(value),4):
        current=value[offset:offset+4]
        if current==replacement[offset:offset+4]:
            merged[offset:offset+4]=original[offset:offset+4]
        elif current!=original[offset:offset+4]:
            preserved.append(offset)
    return bytes(merged),preserved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pid', type=int)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--endpoint', type=int, choices=(128, 256, 512), default=128)
    parser.add_argument('--seconds', type=int, default=90)
    parser.add_argument('--near-fog', type=Path, help='Use numeric fog from the captured near renderer; bounded diagnostic only')
    args = parser.parse_args()
    if not 1 <= args.seconds <= 180:
        parser.error('Duration must be 1..180 seconds')
    report, initial = capture(args.pid)
    if hashlib.sha256(EXE.with_name('hid.dll').read_bytes()).hexdigest() != DLL_HASH:
        raise RuntimeError('Refusing a different native mod installation')
    base = int(report['module_base'], 16)
    pointer = int(report['selected_pointer'], 16)
    if report['fallback'] or not report['pointer_stable']:
        raise RuntimeError('Refusing fallback or unstable atmosphere')
    field_offset=ENDPOINT_OFFSET
    replacement = struct.pack('<f', args.endpoint)
    near, far = struct.unpack_from('<2f', initial, 0x44C)
    if not 0 <= near < far < args.endpoint and not args.near_fog:
        raise RuntimeError('Refusing unexpected fog-grid endpoints')
    candidate=args.endpoint
    original_description=far
    if args.near_fog:
        saved=json.loads(args.near_fog.read_text(encoding='utf-8'))
        replacement=near_fog_payload(saved)
        field_offset=0x3EC
        original_description={'numeric_fog_sha256':hashlib.sha256(initial[field_offset:field_offset+len(replacement)]).hexdigest()}
        candidate={'near_capture':str(args.near_fog.resolve()),'numeric_fog_sha256':hashlib.sha256(replacement).hexdigest()}
        near_position=saved['primary_view_candidates']['0x6739b10']['position_30_raw_floats']
        live_position=report['primary_view_candidates']['0x6739b10']['position_30_raw_floats']
        if sum((a-b)**2 for a,b in zip(near_position,live_position))<50**2:
            raise RuntimeError('Camera is still near the captured position; move far for this diagnostic')
    original = initial[field_offset:field_offset+len(replacement)]

    k = C.WinDLL('kernel32', use_last_error=True)
    k.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
    k.OpenProcess.restype = W.HANDLE
    k.CloseHandle.argtypes = [W.HANDLE]
    k.ReadProcessMemory.argtypes = [W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)]
    k.ReadProcessMemory.restype = W.BOOL
    k.WriteProcessMemory.argtypes = [W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)]
    k.WriteProcessMemory.restype = W.BOOL
    k.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD)]
    k.GetExitCodeProcess.argtypes = [W.HANDLE, C.POINTER(W.DWORD)]
    k.GetExitCodeProcess.restype = W.BOOL
    access = 0x1010 | (0x28 if args.apply else 0)
    handle = k.OpenProcess(access, False, args.pid)
    if not handle:
        raise C.WinError(C.get_last_error())
    changed = False
    outcome = {'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'pid':args.pid,'exe_sha256':EXPECTED,'dll_sha256':DLL_HASH,
               'atmosphere':hex(pointer),'field_offset':hex(field_offset),'write_size':len(replacement),
               'original':original_description,'candidate':candidate,'duration_limit_seconds':args.seconds,
               'writes':0,'applied':False,'restoration':'not_needed',
               'limit':'External reads/writes are not atomic with the renderer. Candidate is not a verified fix.'}

    def read(address, size):
        buffer = C.create_string_buffer(size)
        got = C.c_size_t()
        if not k.ReadProcessMemory(handle, address, buffer, size, C.byref(got)) or got.value != size:
            raise C.WinError(C.get_last_error())
        return buffer.raw

    def write(value):
        got = C.c_size_t()
        buffer = C.create_string_buffer(value)
        if not k.WriteProcessMemory(handle, pointer+field_offset, buffer, len(value), C.byref(got)) or got.value != len(value):
            raise C.WinError(C.get_last_error())
        outcome['writes'] += 1
        if read(pointer+field_offset,len(value)) != value:
            raise RuntimeError('Fog endpoint readback failed')

    def registry():
        return struct.unpack('<Q',read(base+REGISTRY_RVA+0x1C8,8))[0]

    try:
        name = C.create_unicode_buffer(32768)
        size = W.DWORD(len(name))
        if not k.QueryFullProcessImageNameW(handle,0,name,C.byref(size)) or Path(name.value).resolve() != EXE.resolve():
            raise RuntimeError('Process identity changed')
        if not valid_photo(read(base+PHOTO_RVA,0x58),base):
            raise RuntimeError('Refusing outside ordinary Photo Free-camera state')
        if registry() != pointer or read(pointer,BLOCK_SIZE) != initial:
            raise RuntimeError('Atmosphere changed after preflight')
        if args.apply:
            # Mark restoration necessary before attempting the write, including
            # a possible write followed by a failed readback.
            changed = True
            write(replacement)
            outcome['applied'] = True
            print(json.dumps({'event':'fog_profile_applied' if args.near_fog else 'fog_range_applied',
                              'original':original_description,'candidate':candidate,
                              'automatic_restore_seconds':args.seconds}),flush=True)
            deadline = time.monotonic()+args.seconds
            while time.monotonic() < deadline:
                if not valid_photo(read(base+PHOTO_RVA,0x58),base) or registry() != pointer:
                    outcome['stopped_because'] = 'Photo mode or atmosphere changed'
                    break
                if read(pointer+field_offset,len(replacement)) != replacement:
                    outcome['stopped_because'] = 'Native code changed the endpoint'
                    break
                time.sleep(0.25)
        else:
            outcome['dry_run'] = True
    finally:
        if changed:
            try:
                current_pointer = registry()
                header = read(pointer,0x30) if current_pointer == pointer else b''
                value = read(pointer+field_offset,len(replacement)) if current_pointer == pointer else b''
                action = restoration_action(current_pointer,pointer,header,initial[:0x30],value,original,replacement)
                outcome['restoration'] = action
                if action == 'restore':
                    write(original)
                    outcome['restoration'] = 'restored_and_read_back'
                elif action == 'native_value_changed' and args.near_fog:
                    merged,preserved=restore_owned_fields(value,original,replacement)
                    if merged!=value:
                        write(merged)
                    outcome['restoration']='owned_fields_restored_native_changes_preserved'
                    outcome['preserved_native_offsets']=[hex(field_offset+offset) for offset in preserved]
            except (OSError,RuntimeError) as error:
                exit_code = W.DWORD()
                ended = k.GetExitCodeProcess(handle,C.byref(exit_code)) and exit_code.value != 259
                outcome['restoration'] = 'process_ended' if ended else 'RESTORATION_UNVERIFIED_PROCESS_MAY_BE_RUNNING'
                outcome['restoration_error'] = str(error)
        k.CloseHandle(handle)
        directory = ROOT/'work/live-atmosphere-readonly'
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        path = directory/f'{stamp}-fog-{"profile" if args.near_fog else "range"}-probe.json'
        path.write_text(json.dumps(outcome,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(outcome,indent=2),flush=True)
        if outcome['restoration'] == 'RESTORATION_UNVERIFIED_PROCESS_MAY_BE_RUNNING':
            raise RuntimeError('Fog restoration could not be verified in the live process; inspect it before another test')


if __name__ == '__main__':
    main()
