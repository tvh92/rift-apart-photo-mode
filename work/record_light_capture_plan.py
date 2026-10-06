"""Record the next scene-specific diagnostic without modifying the game."""
from pathlib import Path
import json
import hashlib

root = Path(__file__).resolve().parents[1]
statement = ('Next: read-only near/far capture of the six lamps lighting the red bridge near the Emperor statue. '
             'The user says native lamps fade smoothly, but Ctrl makes them blip on/off one by one at a farther point. '
             'This supports a separate hard-edge hypothesis, not an identified cause. Keep installed v2 stable. '
             'Capture uses work/capture_photo_lights_readonly.py, 13 isolated tests and work/light-capture-readonly-review.txt. '
             'It opens QUERY_LIMITED_INFORMATION|VM_READ only, checks exact EXE/DLL, ordinary Photo state4 and primary-view/query ownership; '
             'queue counts/read time are bounded, changing headers are refused, and retired fields are reported. '
             'Transient source/record data remain non-atomic; Ctrl is supplied by the operator, and queue >512 does not prove callback saturation. '
             'Near capture with Ctrl ON is requested; do not reinstall after that request. Then ask for the nearest far position where a lamp blips off while retaining bridge framing, with Ctrl ON, before capturing it. '
             'No code or installed files changed in response to this feedback.')
for name in ('AGENTS.md', 'work/lighting-fog-current.md'):
    path = root / name
    text = path.read_text()
    text = text.replace('No further live capture is needed for this completed installation; future far-camera comparison should assess remaining illumination limits.', statement)
    if name.endswith('lighting-fog-current.md'):
        text = text.replace('Separate indicator testing is explicitly waived; its in-game visibility remains unverified.',
                            'Separate indicator testing was waived at installation; the subsequent user report now confirms the notice works well.')
        text += '\n\n## Lamp diagnostic ready\n\n' + statement + '\n\n' + (
            'Focused static research: work/light-source-cull-followup.txt identifies render/source/category/hierarchy/clip gates and optional-source caps. '
            'A view-relative request uses a48.0 radius field, but its source-result consumer and any general light cutoff are not established. '
            'work/light-lookup-cutoff-followup.txt establishes the FillLightLookup512 cap per callback and an unrelated group mask selector. '
            'Neither is linked to the six lamps without live evidence. work/light-queue-owner-capture-main.txt and work/light-view-query-owner-main.txt establish the captured queue/record/query offsets.\n')
    path.write_text(text)
report = {'installed_dll_unchanged': hashlib.sha256((root / 'outputs/camera-native-lighting-v2/hid.dll').read_bytes()).hexdigest(),
          'status': 'Awaiting near lamp capture; game not running at preparation.',
          'user_landmark': 'Lamp on red bridge near Emperor statue, Corson V; about six lamps, smooth native fade versus hard farther Ctrl cutoff.',
          'process_writes': 0,
          'tests': '13 isolated parser, bounds, ownership-change and retirement tests passed.',
          'review': 'work/light-capture-readonly-review.txt: no blocker; limits retained.',
          'capture_source_sha256': hashlib.sha256((root / 'work/capture_photo_lights_readonly.py').read_bytes()).hexdigest()}
(root / 'work/light-capture-preparation.json').write_text(json.dumps(report, indent=2) + '\n')
print('Read-only capture plan and pending near request recorded; installed DLL unchanged.')
