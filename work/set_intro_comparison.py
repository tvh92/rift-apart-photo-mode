"""Switch only audited intro routing, retaining the installed native DLL.

Run with game and Overstrike closed. --original-movies is a controlled startup
comparison; --short-movies restores the two-second profile. Full audits bracket
the operation, and this run's own snapshots supply rollback on any failure.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart')
MANAGERS = [ROOT/'outputs/Overstrike', Path(r'C:\Users\Tim\Documents\Bestanden\Downloads\Overstrike 1 1.8.1 2026-09-04T22-57Z vzbjnz4Zh')]
PROFILE = 'Profiles/RCRA (Steam).json'


class ProcessEntry(C.Structure):
    _fields_ = [('size',W.DWORD),('usage',W.DWORD),('pid',W.DWORD),
                ('heap',C.c_size_t),('module',W.DWORD),('threads',W.DWORD),
                ('parent',W.DWORD),('priority',W.LONG),('flags',W.DWORD),
                ('name',W.WCHAR*260)]


def assert_closed():
    k=C.WinDLL('kernel32',use_last_error=True)
    k.CreateToolhelp32Snapshot.argtypes=[W.DWORD,W.DWORD];k.CreateToolhelp32Snapshot.restype=W.HANDLE
    k.Process32FirstW.argtypes=[W.HANDLE,C.POINTER(ProcessEntry)]
    k.Process32NextW.argtypes=[W.HANDLE,C.POINTER(ProcessEntry)]
    k.CloseHandle.argtypes=[W.HANDLE]
    handle=k.CreateToolhelp32Snapshot(2,0)
    if handle==C.c_void_p(-1).value:raise C.WinError(C.get_last_error())
    try:
        entry=ProcessEntry();entry.size=C.sizeof(entry)
        ok=k.Process32FirstW(handle,C.byref(entry))
        while ok:
            if entry.name.lower() in ('riftapart.exe','overstrike.exe'):
                raise RuntimeError(f'Close {entry.name} before modifying installation')
            ok=k.Process32NextW(handle,C.byref(entry))
    finally:k.CloseHandle(handle)


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--original-movies',action='store_true')
    group.add_argument('--short-movies',action='store_true')
    args=parser.parse_args()
    assert_closed()
    spec=importlib.util.spec_from_file_location('installation_audit',ROOT/'outputs/camera-controls/Check-Installation.py')
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    before=audit.audit()
    dll=digest(GAME/'hid.dll');ini=digest(GAME/'PhotoModeCamera.ini')
    target=[['NoIntro.stage',False],['PhotoMode-10x-Tether1000.stage',True]]
    if args.short_movies:target.insert(1,['NoIntro-Fixed-2Seconds.stage',True])
    profiles=[json.loads((manager/PROFILE).read_text(encoding='utf-8-sig')) for manager in MANAGERS]
    if all(profile['mods']==target for profile in profiles):
        print('Requested intro profile already installed and audited. No changes.');return
    backup=ROOT/'outputs/startup-repair'/('intro-comparison-'+uuid.uuid4().hex)
    backup.mkdir()
    game_snapshots=[]
    for relative in ['toc','toc.sha1','d/mods/mod0','d/mods/mod1']:
        source=GAME/relative
        if source.exists():
            saved=backup/'game'/relative;saved.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,saved);game_snapshots.append((source,saved))
    for index,manager in enumerate(MANAGERS):
        shutil.copy2(manager/PROFILE,backup/f'profile-{index}.json')
    (backup/'before-audit.json').write_text(json.dumps(before,indent=2)+'\n',encoding='utf-8')
    assert_closed()
    try:
        for manager,profile in zip(MANAGERS,profiles):
            profile['mods']=target
            (manager/PROFILE).write_text(json.dumps(profile,indent=2)+'\n',encoding='utf-8')
        startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
        result=subprocess.run([str(MANAGERS[0]/'Overstrike.exe'),'install-mods','RCRA (Steam)'],cwd=MANAGERS[0],startupinfo=startup,timeout=180,capture_output=True,text=True)
        if result.returncode:raise RuntimeError(f'Overstrike install failed: {result.returncode}\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}')
        after=audit.audit()
        if digest(GAME/'hid.dll')!=dll or digest(GAME/'PhotoModeCamera.ini')!=ini:
            raise RuntimeError('Native DLL/INI changed during asset-only comparison')
        after['native_dll_unchanged']=dll;after['native_ini_unchanged']=ini
        after['intro_comparison']='original full movies' if args.original_movies else 'restored two-second movies'
        after['backup']=str(backup)
        (backup/'after-audit.json').write_text(json.dumps(after,indent=2)+'\n',encoding='utf-8')
        (ROOT/'outputs/startup-repair/current-intro-comparison.json').write_text(json.dumps(after,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'status':'installed and fully audited','intro':after['intro_comparison'],'dll_unchanged':dll,'ini_unchanged':ini,'backup':str(backup)},indent=2))
    except BaseException:
        # Avoid restoring files into a session unexpectedly launched by the user.
        assert_closed()
        for index,manager in enumerate(MANAGERS):shutil.copy2(backup/f'profile-{index}.json',manager/PROFILE)
        for source,saved in game_snapshots:shutil.copy2(saved,source)
        audit.audit()
        raise


if __name__=='__main__':main()
