"""Verify staged/committed bytes, mod snapshots, and optional remote HEAD."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = '16dcd44057c3114b123e25974b9b563afc487650686d3985784614caba5f7cbd'

def git(*args, input=None):
    return subprocess.run(['git', '-c', 'safe.directory=' + ROOT.as_posix(), *args], cwd=ROOT,
                          input=input, capture_output=True, check=True).stdout

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--remote', action='store_true')
    args = parser.parse_args()
    index = []
    for row in git('ls-files', '--stage', '-z').split(b'\0'):
        if not row:
            continue
        metadata, name = row.split(b'\t', 1)
        mode, oid, stage = metadata.split()
        if stage != b'0':
            raise SystemExit('Index has unmerged entries.')
        index.append((oid, name.decode()))
    if not index:
        raise SystemExit('No staged project files.')
    forbidden = ('work/live-lights-readonly/', 'work/live-atmosphere-readonly/', 'work/zig-cache/',
                 'work/disasm/', 'outputs/Overstrike/')
    for _, name in index:
        if name.startswith(forbidden) or (name.startswith('work/toolchain/') and name != 'work/toolchain/zig-download.json'):
            raise SystemExit('Local-only dependency/capture was staged: ' + name)
    blobs = git('cat-file', '--batch', input=b'\n'.join(oid for oid, _ in index) + b'\n')
    cursor = 0
    size_sum = 0
    for oid, name in index:
        end = blobs.index(b'\n', cursor)
        got_oid, kind, size_bytes = blobs[cursor:end].split()
        size = int(size_bytes)
        start = end + 1
        body = blobs[start:start + size]
        if got_oid != oid or kind != b'blob' or blobs[start + size:start + size + 1] != b'\n':
            raise SystemExit('Unexpected Git object stream.')
        current = (ROOT / name).read_bytes()
        if hashlib.sha256(body).digest() != hashlib.sha256(current).digest():
            raise SystemExit('Git bytes differ from local file: ' + name)
        cursor = start + size + 1
        size_sum += size
    expected_files = {'README.md', 'AGENTS.md', 'CONTINUE-PHOTO-MODE.md', 'migration/local-artifacts.json',
                      'outputs/camera-native-lighting-v2/hid.dll',
                      'outputs/confirmed-photo-fog/2026-10-05/hid.dll',
                      'work/bridge-light-cutoff-bracket.json', 'work/bridge-light-query-handle-proof-main-luna.txt'}
    if not expected_files.issubset({name for _, name in index}):
        raise SystemExit('Expected current package/research files are missing.')
    native = ROOT / 'outputs/camera-native-lighting-v2/hid.dll'
    installed = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\hid.dll')
    if hashlib.sha256(native.read_bytes()).hexdigest() != EXPECTED:
        raise SystemExit('Current package hash changed.')
    installed_hash = hashlib.sha256(installed.read_bytes()).hexdigest() if installed.exists() else None
    report = {'staged_files': len(index), 'staged_bytes': size_sum, 'all_git_bytes_match_local_files': True,
              'installed_dll_sha256': installed_hash, 'installed_dll_matches_current_package': installed_hash == EXPECTED,
              'local_only_directories_absent_from_git': True,
              'repository': 'https://github.com/tvh92/rift-apart-photo-mode'}
    if args.remote:
        head = git('rev-parse', 'HEAD').decode().strip()
        remote = git('ls-remote', 'origin', 'refs/heads/main').decode().split()[0]
        if head != remote:
            raise SystemExit('Remote main differs from local HEAD.')
        if git('status', '--porcelain'):
            raise SystemExit('Tracked/unignored working files remain uncommitted.')
        report.update(commit=head, remote_main=remote, clean_worktree=True)
        (ROOT / 'migration/remote-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
