"""Inventory this project for GitHub without touching game files or credentials."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DEPENDENCIES = ['work/toolchain', 'work/zig-cache', 'work/disasm', 'outputs/Overstrike']
SECRET_PATTERNS = [
    re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(rb'\bgh[pousr]_[A-Za-z0-9]{30,}\b'),
    re.compile(rb'\bgithub_pat_[A-Za-z0-9_]{50,}\b'),
    re.compile(rb'\bAKIA[A-Z0-9]{16}\b'),
]

def git(*args, input=None):
    result = subprocess.run(['git', '-c', 'safe.directory=' + ROOT.as_posix(), *args],
                            cwd=ROOT, input=input, capture_output=True)
    if result.returncode not in (0, 1):
        raise SystemExit('Git inventory failed: ' + result.stderr.decode(errors='replace'))
    return result

def main():
    command = ['rg', '--files', '--hidden', '--no-ignore', '-g', '!.git/**', '-g', '!**/__pycache__/**']
    command += [item for dep in DEPENDENCIES for item in ('-g', '!' + dep + '/**')]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, check=True)
    paths = sorted(Path(name).as_posix() for name in result.stdout.decode().splitlines())
    paths += ['work/toolchain/zig-download.json']
    paths = sorted(set(paths))
    ignored_result = git('check-ignore', '--no-index', '-z', '--stdin',
                         input=b'\0'.join(p.encode() for p in paths) + b'\0')
    ignored = set(ignored_result.stdout.decode().strip('\0').split('\0'))
    tracked = []
    local = []
    failures = []
    for name in paths:
        path = ROOT / name
        size = path.stat().st_size
        sha = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                sha.update(chunk)
                if name not in ignored and any(p.search(chunk) for p in SECRET_PATTERNS):
                    failures.append({'path': name, 'reason': 'Potential credential material'})
        item = {'path': name, 'bytes': size, 'sha256': sha.hexdigest()}
        if name in ignored:
            item['reason'] = ('raw process capture' if name.startswith(('work/live-atmosphere-readonly/',
                            'work/live-lights-readonly/')) else 'local binary, game asset, or build product')
            local.append(item)
        else:
            if size >= 50 * 1024 * 1024:
                failures.append({'path': name, 'reason': 'Tracked file exceeds migration size bound'})
            tracked.append(item)
    folder = ROOT / 'migration'
    folder.mkdir(exist_ok=True)
    (folder / 'local-artifacts.json').write_text(json.dumps({
        'policy': 'These files remain intact locally and are excluded from Git. No assets were deleted.',
        'local_workspace': str(ROOT),
        'dependency_directories_excluded_without_hashing': DEPENDENCIES,
        'regenerable_directories_excluded': ['**/__pycache__'],
        'artifacts': local,
    }, indent=2) + '\n')
    report = {'tracked_file_count_before_manifest': len(tracked),
              'tracked_bytes_before_manifest': sum(x['bytes'] for x in tracked),
              'local_artifact_count': len(local), 'local_artifact_bytes': sum(x['bytes'] for x in local),
              'credential_scan': 'passed' if not failures else 'failed',
              'limits': 'High-confidence token/private-key scan; not a comprehensive secret detector.',
              'failures': failures,
              'own_proxy_dlls': [x for x in tracked if x['path'].endswith('/hid.dll')],
              'tracked_extension_counts': {suffix: sum(Path(x['path']).suffix.lower() == suffix for x in tracked)
                                          for suffix in sorted({Path(x['path']).suffix.lower() for x in tracked})}}
    (folder / 'pre-push-audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'own_proxy_dlls'}, indent=2))
    if failures:
        raise SystemExit('Migration audit refused the planned files.')

if __name__ == '__main__':
    main()
