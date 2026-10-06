from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[1]
package = root / 'outputs/camera-native-lighting-v2'
manifest = json.loads((package / 'build-verification.json').read_text())
expected = '16dcd44057c3114b123e25974b9b563afc487650686d3985784614caba5f7cbd'
assert manifest['installed'] and manifest['dll_sha256'] == expected
game_dll = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\hid.dll')
assert hashlib.sha256(game_dll.read_bytes()).hexdigest() == expected

current = """**Currently installed (6 October):** lighting-v2 DLL `16dcd44057c3114b123e25974b9b563afc487650686d3985784614caba5f7cbd`, package `outputs/camera-native-lighting-v2`. Extends the previous RGB far-fade override to ordinary specular bit20 and the separate type4 far fade. Ctrl still controls the Photo-only detail override, including the unchanged confirmed fog implementation and the fading ON/OFF notice. User explicitly waived a separate indicator test and requested continued lighting work; do not ask for that UI test. Local native/UI probes, actual-source review and full pre/post installation audits pass. The new lighting behavior and indicator visibility in-game remain unconfirmed. Original movies, INI and assets are preserved. `Restore-PreviousStatus.ps1` returns to exact status770; its `Restore-TestedLighting.ps1` can then return to testedfa3. Use only the guarded package scripts with the game closed. No further live capture is needed for this completed installation; future far-camera comparison should assess remaining illumination limits."""

agents = root / 'AGENTS.md'
text = agents.read_text(encoding='utf-8')
start = text.index('**Currently installed (6 October):**')
end = text.index('\n\n', start)
text = text[:start] + current + text[end:]
text = text.replace('Current status770 includes the unchanged fog/light implementations plus user-requested indicator.', 'Current lighting-v2 retains confirmed fog and the indicator, while extending the far-light fade bypass; see the current installed paragraph.')
text = text.replace('Current installed status770 and partial lightingfa3 result are described at the top.', 'Current installed lighting-v2 and partial lightingfa3 result are described at the top.')
agents.write_text(text, encoding='utf-8')

doc = root / 'work/lighting-fog-current.md'
text = doc.read_text(encoding='utf-8')
start = text.index('**Current installed status candidate:**')
end = text.index('\n\n', start)
text = text[:start] + current + text[end:]
text = text.replace('## Ordinary surface lights\n', '## Ordinary surface lights\n\nThe fa3 implementation and its original limitations below describe the first lighting release. The installed v2 extends it as documented in the final section. The current unwind probe checks all 29 real instruction starts; arbitrary interior bytes are not valid unwind test PCs.\n')
text = text.replace('No lighting code has changed.', 'That feasibility report predates the implemented fa3 and v2 lighting hooks.')
text = text.replace('Next: ordinary light RGB-to-shader/constructor/query tracing before a separate Photo-only illumination override.', 'The ordinary RGB/specular shader bridge and Photo-only lighting hooks have since been implemented; see the lighting sections.')
text += """

## Installed lighting-v2, 6 October

The earlier RGB-only bypass can retain colour while the ordinary helper's separate bit20 fade still reduces specular intensity to zero and changes the output type. V2 clears local bits18+20 before the native helper continues, preserving source specular intensity and type at distance. The relay's existing primary-view/caller/Photo/Ctrl gates and native near fade remain intact. Source light objects are never changed.

Type4 uses helper1098F90 separately. The new PhotoSpecular.h changes only the CALL displacement at10BE261, within the aligned8-byte word10BE260. A leaf relay reaches a compiled wrapper, which copies the B0-byte light prefix, clears far flag18 in the private copy and calls the original once. Adjacent bytes, native near fade, source data and off/auxiliary-view behavior are preserved. Both hooks remain exact-build guarded and reversible.

Validation: 1920 actual-native ordinary cases, all29 real relay instruction-start unwind comparisons, 24 actual-native type4 cases, source/near-fade preservation, exact-site/prolog refusal, Ctrl/readiness/auxiliary-view gates and atomic restoration pass. A concrete case reproduces the first release's gap: RGB-only retains colour but specular becomes0/type1; v2 retains0.7/type0. A type4 example changes native0.5 at distance85 to retained1. Fog, lifecycle, camera/no-clip, UI and44 HID-export checks also pass. Log: work/specular-candidate-build-test.log. Actual-source review: work/photo-specular-actual-source-review.txt; no blocker found. These fixtures do not establish user-visible success in the game.

Install-SpecularCandidate.ps1 completed with the game closed. Candidate/installed hash16dcd44057c3114b123e25974b9b563afc487650686d3985784614caba5f7cbd and rollback77051506a589b1051556505b309c32eb7a4a69e93df93d0a29d85b74b045a2d0 were read back. Pre/post complete audits pass and all non-DLL fields match. INI2742e230e680046e4833173c6a435822aaa319999d9626608381118ad7ff34e9 is unchanged. Evidence: outputs/camera-native-lighting-v2/{build-verification,pre-installation-audit,installation-audit}.json. Separate indicator testing is explicitly waived; its in-game visibility remains unverified. Do not mark all distant lights/shadows fixed.

Remaining spatial gates:109A670's size/distance predicate puts lights into a secondary list that is later submitted too;10B7330 controls auxiliary-volume rebuilding, not final rejection. Neither proves a hard light range.1604440 can reject candidates using clip constraints; category/resource/hierarchy filters, streaming and the FillLightLookup512-entry cap also remain native. Do not bypass these speculatively. Read-only evidence: work/ordinary-light-pre-fade-exclusions-luna.txt and work/lightsubmit-spatial-gates-luna.txt. The ordinary RGB/specular GPU-buffer bridge is already proven; additional clip-volume consumers and any remaining runtime disappearance cause are unresolved.
"""
doc.write_text(text, encoding='utf-8')

report = root / 'work/lightsubmit-spatial-gates-luna.txt'
text = report.read_text(encoding='utf-8')
text = text.replace('The final GPU upload/consumer path is still unproven.', 'Parent reconciliation: the ordinary RGB/specular FillLightLookup GPU-buffer bridge is already proven in work/surface-light-filllookup-bridge.txt and reflected shader offsets. The additional clip-volume consumer and any remaining runtime disappearance cause are unproven.')
report.write_text(text, encoding='utf-8')
print('Current installed lighting-v2 state and validation recorded; spatial evidence reconciled.')
