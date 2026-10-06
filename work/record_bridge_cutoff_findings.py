"""Retain completed read-only bridge comparison and correct observer limits."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[1]
note = """### Completed bridge cutoff captures, 6 October

The user supplied three stationary Ctrl-ON positions in PID9236: near, beyond the first visible cutoff, and back inside it. Capture paths and comparisons are retained in `work/bridge-light-near-far-comparison.json` and `work/bridge-light-cutoff-bracket.json`. Near: six accepted samples,91 pass67 records each. Far: six accepted samples,135 or141 records. Inside: two accepted samples,143 records each. A tentative six-light spatial group has radius25. Its z~42 pair is present in every near/inside sample and absent in every far sample; the other four retain exactly identical RGB across near/far. This supports pre-upload submission exclusion rather than another brightness-fade explanation, but position matching does not prove source identity or the precise gate. The closer/far center-distance bracket is about137..166 world units; it is not an exact LOD threshold. No process writes or installed-file changes were made.

Observer correction: passBB is a null-argument queue marker; the frame job is returned separately. The earlier passBB-param+18 query claim in the initial review is retracted. The far capture's one error per sample is the obsolete attempted passBB null read, not a failed pass67 record read. Raw captures are preserved. The current observer removes this path. Archive reserved capacity16384 is allowed while populated count remains bounded8192; unused capacity is not read.

Typed source-query observation remains unresolved. Callback12B8740 and manager674EC10 identify request slots; slot68 is the output array and slot70 the output-count pointer (slot50 is filter context). Deriving query from counter-10/-20 finds the primary owner, but the request output pointer differs from current query8/18. The observer refuses all such source-array reads rather than weakening identity guards. Latest metadata: `work/live-lights-readonly/20261005T231220416213Z-bridge-query-pointer-proof.json`, six accepted queue samples143 each, zero validated source queries, zero writes. These pointer candidates alone are not source captures. Eighteen isolated observer tests pass. Further work should trace query lifecycle/selection or prepare bounded in-process diagnostics with exact ABI/build guards. User was told they can close the game; do not require another live positioning session until a concrete diagnostic is ready.
"""

for name in ('AGENTS.md', 'work/lighting-fog-current.md'):
    path = root / name
    text = path.read_text()
    start = text.index(' Next: read-only near/far capture')
    end = text.index('\n', start)
    text = text[:start] + ' Read-only bridge captures are complete; see the completed-capture note below. Keep installed v2 stable; remaining illumination cutoff is unresolved.' + text[end:]
    if '### Completed bridge cutoff captures, 6 October' not in text:
        insertion = text.index('\n\n', start) + 2
        text = text[:insertion] + note + '\n' + text[insertion:]
    path.write_text(text)

path = root / 'work/light-capture-preparation.json'
data = json.loads(path.read_text())
data['preparation_status_historical'] = data['status']
data['preparation_source_sha256_historical'] = data['capture_source_sha256']
data.update(status='Completed near/far/inside bridge queue captures; exact source selection gate unresolved.',
            tests='18 isolated parser, bounds, ownership-change and retirement tests passed.',
            capture_source_sha256=hashlib.sha256((root / 'work/capture_photo_lights_readonly.py').read_bytes()).hexdigest(),
            source_queries_validated=0,
            comparison_reports=['work/bridge-light-near-far-comparison.json', 'work/bridge-light-cutoff-bracket.json'],
            corrections=['passBB marker has null parameters; old query derivation retracted',
                         'reserved archive capacity16384 does not imply reading16384 entries',
                         'request output slot68; slot50 is filter context'])
path.write_text(json.dumps(data, indent=2) + '\n')

path = root / 'work/light-capture-readonly-review.txt'
text = path.read_text()
correction = '\nParent correction after live capture, 6 October:\nThe passBB/framejob-query assertion above is retracted:12BC6BF queues a null-argument marker, not the returned frame job. Current observer removes that path. Reserved archive capacity16384 is permitted while populated count is bounded8192. Typed request slots use callback12B8740/manager674EC10, output slot68 and counter slot70; no source query has passed current array-pointer equality.18 isolated tests pass. See completed bridge captures in work/lighting-fog-current.md.\n'
if 'Parent correction after live capture' not in text:
    path.write_text(text + correction)
print('Retained completed bridge comparison and observer corrections; installed files unchanged.')
