"""Record installed UI and the user's explicit waiver of its separate test."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
candidate=root/'outputs/camera-native-status-candidate'
manifest=json.loads((candidate/'build-verification.json').read_text(encoding='utf-8-sig'))
assert manifest['installed'] and manifest['dll_sha256']=='77051506a589b1051556505b309c32eb7a4a69e93df93d0a29d85b74b045a2d0'
manifest['runtime_status']='User explicitly waived separate indicator test and requested continued lighting work; indicator startup/visibility unverified.'
manifest['user_steering']='skip testing this one, continue with the lighting stuff'
(candidate/'build-verification.json').write_text(json.dumps(manifest,indent=2)+'\n')
p=root/'AGENTS.md';text=p.read_text()
first=next(line for line in text.splitlines() if line.startswith('**Currently installed,'))
current='**Currently installed (6 October):** status candidate DLL `77051506a589b1051556505b309c32eb7a4a69e93df93d0a29d85b74b045a2d0`, package `outputs/camera-native-status-candidate`. User requested the fading ON/OFF indicator again, then explicitly said "skip testing this one, continue with the lighting stuff". Do not ask for a separate UI test. Indicator startup/visibility remain unverified; local native/UI probes, visual preview, source review and complete installation audit pass. Ctrl flashes Detail override ON/OFF,900ms hold/700ms fade. Worker starts only valid focused Photo state4 entry/toggle; loading creates no UI thread/window. Camera/geometry/fog/light implementation files match tested lightingfa3 exactly; only PhotoLOD UI integration and PhotoIndicator.h change. Original movies/INI/assets preserved. Rollback `Restore-TestedLighting.ps1` returns to testedfa3 without UI. Continue investigating remaining lighting exclusions in a separate candidate; keep installed files stable until the next concrete lighting result is ready.'
text=text.replace(first,current)
first=next(line for line in text.splitlines() if line.startswith('**Current user-confirmed working build:**'))
text=text.replace(first,'**User-confirmed fog release:** DLL2286 `228620169d5741cd57d544047d351e7bd3c7df541778bc78c17ea0655bcb6f2a`, exact source/DLL snapshot `outputs/confirmed-photo-fog/2026-10-05`. Preserve it. Lightingfa3 result is partial: user thinks it works, but reports a farther light disappearance distance with Ctrl enabled. Real log confirms startup/Photo/Ctrl and867005 primary-light relay applications. Exact testedfa3 source/DLL/log snapshot: `outputs/tested-photo-lighting/2026-10-06`. Do not mark illumination completely fixed. Remaining ordinary-light exclusions are unresolved; focused trace `work/ordinary-light-pre-fade-exclusions-luna.txt`. Current status770 includes the unchanged fog/light implementations plus user-requested indicator.')
text=text.replace('Updated 5 October 2026.','Updated 6 October 2026.')
text=text.replace('Current installed separate lighting candidatefa3 is described at the top.','Current installed status770 and partial lightingfa3 result are described at the top.')
p.write_text(text)
p=root/'work/lighting-fog-current.md';text=p.read_text()
first=next(line for line in text.splitlines() if line.startswith('**Current installed separate lighting candidate:**'))
current='**Current installed status candidate:** `77051506a589b1051556505b309c32eb7a4a69e93df93d0a29d85b74b045a2d0`, package `outputs/camera-native-status-candidate`. User requested a fading ON/OFF notice, then explicitly waived its separate test and asked to continue lighting work. Local UI/native probes, visual preview, source review and complete installation audit pass. Indicator in-game startup/visibility remain unverified. Existing camera/geometry/fog/light implementation files match tested lightingfa3; Ctrl semantics are unchanged. Original full intro movies, INI and assets remain unchanged. Rollback to exact tested lightingfa3 exists; confirmed fog2286 remains preserved separately.'
text=text.replace(first,current)
text+='\n## Latest user feedback and steering, 6 October\n\nUser thinks lightingfa3 works but reports a second, farther disappearance distance with Ctrl on. Treat this as partial improvement, not a full cure. Log records867005 applications of the primary light relay at teardown, confirming it actually ran; source/DLL/log/feedback snapshot is `outputs/tested-photo-lighting/2026-10-06`. The game was closed before status770 installation. User has explicitly waived a separate indicator test and wants remaining lighting work to continue. Do not ask for that UI test. Bounded read-only followup traces ordinary eligibility/frustum/volume callbacks; do not infer a hard range from ranking or guess a new global override.\n'
p.write_text(text)
print('Installed status770 and explicit skipped UI test recorded; lighting remains partial.')
