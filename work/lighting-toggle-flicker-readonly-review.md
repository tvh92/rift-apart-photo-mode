# Lighting toggle and flicker review (read-only)

Supported build: RiftApart.exe SHA256 `51299faca6...6d82`; inspected the installed-v3 snapshot sources and preserved exact-build traces. No source, installation, game, or process changes were made.

## Ctrl comparison behavior

Ctrl intentionally toggles the combined geometry, lighting, and fog comparison. `PhotoLOD.h` sets `geometry_active = session && geometry_enabled`; `PhotoLight.h`, `PhotoSpecular.h`, and `PhotoCutoff.h` use this shared gate. Turning detail/comparison OFF therefore restores native light fades and the native pre-upload cutoff. This is expected behavior and is not a confirmed bug. The user-reported nearby light disappearance is not explained by this intended gate behavior; its cause remains unresolved.

## Input polling observation (effect unproven)

`toggle_photo_geometry` samples `GetAsyncKeyState(VK_CONTROL)` three times in one boolean expression, then edge-detects with `lod_toggle_down`. The repeated reads are unnecessary and could disagree if the key changes during the expression. Polling occurs from `HookPhotoTick`, so a press and release entirely between callback invocations would not be observed. A press observed outside the ready/enabled, setup-byte, foreground-process, state-4 conditions also does not toggle. These are source-level observations; no input-path test or tick-cadence measurement establishes that they caused the reported poor responsiveness. Treat them as a candidate for focused validation, not a diagnosed cause.

## Query/cache and asynchronous frame boundaries

`work/light-query-array-producer.md` proves that fresh query construction calls `0x10BB270`, which waits for gathers, swaps `[q+8]` to a new buffer and schedules filter job `0x10B9A50`; a reused query (`view+0x11DA`) skips both construction and that filtering setup. The worker writes to its captured output pointer, while `0x10BA710` ranks the current query array and waits on `q+0x78`. Thus raw slot output and current query input are distinct products, and observer snapshots need not represent one frame. The preserved token guard establishes request ownership identity but does not make asynchronous snapshots frame-atomic.

Follow-up caller analysis in `light-query-reuse-toggle-response-readonly.md` establishes that all three indexed direct frame callers fail the reuse prerequisites and build a fresh query. Stale query reuse is therefore withdrawn as an explanation for these paths; a stable pointer can be allocator reuse. A worker already in flight still reads the shared comparison gate when it reaches the branch, but a visible toggle race remains unproven. Existing captures do not tie mixed frame snapshots to a specific missing nearby light.

## Remaining native exclusions

V3 bypasses only the early bit-18 front-of-bounds drop at `0x10B9C07` for the primary Photo view while the comparison gate is active. Eligibility bits, near fade, type/colour eligibility, occlusion (`0x118CDC0`), ranking/sorting, duplicate rules, shader/cluster selection and downstream limits remain native. The 512 cap at `0x10BAC78` only limits secondary merges; if primaries fill 512, secondaries are skipped. These are plausible candidate stages for distant flicker or missing lights, but none is identified as the cause by the reviewed evidence. Native cutoff/nearfade rules may explain intended OFF behavior; they do not establish why a nearby light disappears when expected to remain visible.

The preserved bridge captures established a prior exact bit-18/A0 cutoff cause, and v3 targets it; the handoff says runtime comparison with Ctrl ON was pending. Those captures do not establish whether v3 resolved the bridge lamps or explain the current nearby-light report.

## Smallest next diagnostic

Keep the combined Ctrl semantics unchanged. First compare ON/OFF at a nearby missing light while recording the same light's presence at query input, post-filter list, and submitted record, together with the comparison gate state and a single frame/query generation marker. If the source disappears before query input, investigate producer/cache ownership; if it disappears at filtering, capture the precise native rejection reason; if it survives submission, inspect downstream GPU/cluster selection. Keep the capture bounded to the identified light and neighboring frames. This separates observed evidence from candidate causes without widening native filters speculatively.
