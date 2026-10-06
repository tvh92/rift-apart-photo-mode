"""Record the user's actual comparison without promoting local probes to success."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil

root = Path(__file__).resolve().parents[1]
game = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart')
folder = root / 'outputs/camera-native-lighting-v2'
expected = '16dcd44057c3114b123e25974b9b563afc487650686d3985784614caba5f7cbd'
for path in (game / 'hid.dll', folder / 'hid.dll'):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
log = (game / 'PhotoModeCamera.log').read_text()
for marker in ('Photo primary surface-light colour/specular fade override installed',
               'Photo type4 specular fade override installed',
               'Photo status indicator ready after active Photo Mode entry',
               'Photo surface-light primary relay applications=291014.'):
    assert marker in log, marker
feedback = {
    'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'dll_sha256': expected,
    'user_report': 'can confirm the notice works well, but the lighting stuff stays the same as before',
    'indicator_status': 'User-confirmed working in game.',
    'lighting_status': 'No additional visible lighting improvement over the prior RGB-only fix; remaining cutoff unresolved.',
    'runtime_evidence': 'Both light hooks installed; Photo/Ctrl and notice initialized; shared light counter291014 at teardown. Counter does not distinguish ordinary/type4 hits.',
}
manifest = json.loads((folder / 'build-verification.json').read_text())
manifest['runtime_status'] = feedback['lighting_status']
manifest['indicator_runtime_status'] = feedback['indicator_status']
manifest['runtime_feedback'] = feedback
(folder / 'build-verification.json').write_text(json.dumps(manifest, indent=2) + '\n')
snapshot = root / 'outputs/tested-photo-lighting-v2/2026-10-06'
snapshot.mkdir(parents=True, exist_ok=True)
for path in folder.iterdir():
    if path.is_file() and path.suffix in ('.c', '.h', '.S', '.def', '.dll', '.md', '.json', '.ps1'):
        target = snapshot / path.name
        if target.exists():
            assert target.read_bytes() == path.read_bytes(), target
        else:
            shutil.copy2(path, target)
shutil.copy2(game / 'PhotoModeCamera.log', snapshot / 'PhotoModeCamera.log')
(snapshot / 'runtime-feedback.json').write_text(json.dumps(feedback, indent=2) + '\n')

agents = root / 'AGENTS.md'
text = agents.read_text()
text = text.replace('The new lighting behavior and indicator visibility in-game remain unconfirmed.',
                    'User now confirms the notice works well, but lighting remains the same as before: no additional visible improvement from v2. Both lighting hooks installed and the shared relay counter291014 is logged; it does not distinguish hook types. Preserve source/DLL/log/feedback snapshot outputs/tested-photo-lighting-v2/2026-10-06. Remaining illumination cutoff is unresolved.')
agents.write_text(text)
doc = root / 'work/lighting-fog-current.md'
text = doc.read_text()
text = text.replace('The new lighting behavior and indicator visibility in-game remain unconfirmed.',
                    'User confirms the notice works well, but reports no additional lighting improvement from v2; the remaining cutoff is unresolved.')
text += '\n\n## User comparison after v2, 6 October\n\n' + feedback['user_report'] + '\n\n' + feedback['runtime_evidence'] + ' Exact tested source/DLL/log/feedback retained in outputs/tested-photo-lighting-v2/2026-10-06. Notice is now runtime-confirmed; lighting remains partially improved as in fa3. Keep installed v2 stable while tracing pre-submission eligibility and downstream lookup selection. No speculative clip/cap/range bypass is justified by this result.\n'
doc.write_text(text)
print('Recorded confirmed notice and unchanged remaining lighting cutoff; tested v2 preserved.')
