"""Preserve tested v3 sources and record partial feedback, without game writes."""
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
from inspect_game_minidump import inspect

root = Path(__file__).resolve().parent.parent
package = root / 'outputs/camera-native-lighting-v3'
game = Path('C:/Program Files (x86)/Steam/steamapps/common/Ratchet & Clank - Rift Apart')
expected_dll = 'c4be06b9e069829ba3c173ab3545353f38de04d6a98c5f58533af42ae9efbe66'
expected_exe = '51299faca61866cf10ea9035a15b8f22600a56557dd5ffc1aad390d5a54e6d82'
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
if sha(game / 'RiftApart.exe') != expected_exe or any(
        sha(path) != expected_dll for path in (package / 'hid.dll', game / 'hid.dll')):
    raise RuntimeError('Current v3 build guard failed; no feedback files changed.')
snapshot = root / 'outputs/tested-photo-lighting-v3/2026-10-06'
snapshot.mkdir(parents=True, exist_ok=True)
manifest = json.loads((package / 'build-verification.json').read_text(encoding='utf-8-sig'))
for name, expected in manifest['source_hashes'].items():
    if sha(package / name).lower() != expected.lower():
        raise RuntimeError('Recorded v3 source hash mismatch: ' + name)
names = list(manifest['source_hashes']) + ['hid.dll', 'export-manifest.json',
    'build-verification.json', 'installation-audit.json', 'pre-installation-audit.json',
    'proxy-test.json', 'README.md']
for name in names:
    source, target = package / name, snapshot / name
    if target.exists():
        if name not in ('README.md', 'build-verification.json') and sha(target) != sha(source):
            raise RuntimeError('Existing snapshot differs: ' + name)
    else:
        shutil.copy2(source, target)

dump_dir = Path('C:/Users/Tim/Documents/Ratchet & Clank - Rift Apart')
dump_names = ['Ratchet & Clank - Rift Apart-v3.630.1.0 2026-10-06-13-33-46.mdmp',
              'Ratchet & Clank - Rift Apart-v3.630.1.0 2026-10-06-13-35-39.mdmp']
reports = [inspect(dump_dir / name) for name in dump_names]
(root / 'work/sargasso-crash-readonly-summary.json').write_text(json.dumps(reports, indent=2) + '\n')
feedback = {
    'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'exe_sha256': expected_exe, 'installed_dll_sha256': expected_dll,
    'runtime_status': 'Partial lighting improvement; flicker, toggle response and nearby OFF-light disappearance unresolved.',
    'user_feedback': [
        'I tested it in-game btw and the lighting works fairly well but still tends to flicker at large distances',
        "it also doesn't respond very well after toggling Ctrl on/off, I also have seen instances of some lights explicitly turning off when detail is turned off despite me being right next to them",
        'also on Sargasso, if I fly too far into the sky the game abruptly crashes',
        'similarly on Sargasso, there is a LOT of dust in the air, maybe this can be filtered out?'],
    'sargasso_crash_ctrl_override': 'ON (user confirmed)',
    'crash_evidence': {
        'report': 'work/sargasso-crash-readonly-summary.json',
        'system_events': 'work/sargasso-display-events.json',
        'observed': 'Both dumps embed NRI D3D12 Map failure 0x887A0005; matching Display 4101 events report driver recovery.',
        'failure_class': 'DXGI_ERROR_DEVICE_REMOVED / graphics device loss',
        'root_cause': 'Unresolved; no GetDeviceRemovedReason/DRED evidence recovered.'},
    'proxy_log_limitation': 'Current installed PhotoModeCamera.log has only unsupported-executable forwarding lines; it cannot verify hooks in either crashed game session.',
    'changes_in_response': 'Read-only diagnostics and documentation only; no installed DLL/INI/assets/settings/saves changed.',
    'snapshot_hashes': {name: sha(snapshot / name) for name in names}}
(snapshot / 'runtime-feedback.json').write_text(json.dumps(feedback, indent=2) + '\n')
manifest['runtime_status'] = feedback['runtime_status']
manifest['runtime_feedback'] = 'outputs/tested-photo-lighting-v3/2026-10-06/runtime-feedback.json'
manifest['limitations'] = ('Runtime improvement is partial. Distant flicker, poor toggle response and nearby OFF-light disappearance remain unresolved. '
    'Sargasso sky crash with Ctrl ON corresponds to graphics-device loss/driver recovery; its cause is unproven. '
    'Native occlusion, near fade, ranking, secondary merge cap and GPU limits remain.')
original_manifest = (snapshot / 'build-verification.json').read_bytes()
manifest_text = original_manifest.decode('utf-8-sig')
for field in ('runtime_status', 'limitations'):
    manifest_text, matched = re.subn(r'("' + field + r'"\s*:\s*)"(?:\\.|[^"\\])*"',
        lambda match: match[1] + json.dumps(manifest[field]), manifest_text)
    if matched != 1:
        raise RuntimeError('Ambiguous manifest feedback field: ' + field)
newline = '\r\n' if '\r\n' in manifest_text else '\n'
manifest_text = manifest_text.rstrip()
if not manifest_text.endswith(newline + '}'):
    raise RuntimeError('Unexpected manifest closing layout')
manifest_text = manifest_text[:-len(newline + '}')] + ',' + newline + '    "runtime_feedback":  ' + json.dumps(manifest['runtime_feedback']) + newline + '}' + newline
bom = b'\xef\xbb\xbf' if original_manifest.startswith(b'\xef\xbb\xbf') else b''
(package / 'build-verification.json').write_bytes(bom + manifest_text.encode('utf-8'))
update = ('**Runtime update, 6 October:** user reports lighting works fairly well, but distant flicker, poor Ctrl response and nearby lights disappearing with Ctrl OFF remain. '
    'Sargasso sky crash occurred with Ctrl ON; both recent dumps contain NRI D3D12 Map error 0x887A0005 and matching Windows driver-recovery events. '
    'The triggering renderer workload/path is unresolved. Current installed v3 is preserved; this investigation has made no game-file/settings/process changes. '
    'Tested source/DLL/feedback snapshot: `outputs/tested-photo-lighting-v3/2026-10-06`. '
    'Read `work/lighting-v3-runtime-followup.md`; no crash-height reproduction is requested.**')
for name in ('AGENTS.md', 'work/lighting-fog-current.md'):
    path = root / name
    text = path.read_bytes().decode('utf-8')
    text = text.replace('**Runtime bridge comparison with Ctrl ON is pending.**', update)
    path.write_bytes(text.encode('utf-8'))
path = package / 'README.md'
text = path.read_bytes().decode('utf-8').replace('**Runtime comparison pending.**',
    '**Runtime result partial:** improved lighting, with distant flicker/toggle and nearby OFF-light issues unresolved. '
    'Sargasso sky crash with Ctrl ON has graphics-device-loss evidence; cause unresolved. '
    'See `work/lighting-v3-runtime-followup.md` and `outputs/tested-photo-lighting-v3/2026-10-06/runtime-feedback.json`.')
path.write_bytes(text.encode('utf-8'))
print(json.dumps({'snapshot': str(snapshot), 'dll_sha256': expected_dll,
                  'runtime': feedback['runtime_status'], 'game_writes': 0}))
