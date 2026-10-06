# Photo Mode light far-cutoff candidate (lighting-v3)

Installed 6 October 2026 with the game closed; full pre/post audits passed. **Runtime comparison pending.**

Cause: after the light-grid gather, job `0x10B9A50` rebuilds the LightSubmit query array and drops any light with flag bit18 whose front-of-bounds distance (`0x10B9750`) exceeds `rec+0xA0` (`0x10B9C00` comiss, `0x10B9C07` ja). The Corson V bridge lamps use 150. Natively their fade reaches zero by then; lighting-v2 removed that fade for Photo/Ctrl, so lamps stayed bright until this drop removed them one by one. Live captures matched the formula at four camera positions (`work/bridge-light-next-diagnostic.md`).

Change: `PhotoCutoff.h` replaces the aligned 8 bytes at `0x10B9C00` with a JMP to a leaf relay. If ready, Ctrl override active, and the job's view (`[rsp+38h]` = view+0x30) is the primary view `[0x6739B10]`, the light is kept; otherwise the original compare/branch is replayed exactly. RAX is restored (`0x10B9750` never writes it); flags are dead at both targets; registered CHAININFO unwind matches the native frame. A counter is logged at Photo teardown ("Photo light far-cutoff retentions="). All other filters (eligibility, near fade, type/colour, occlusion, 512 merge cap) stay native. All v2 sources are byte-identical except `PhotoLOD.h` wiring/logging.

Tests: `work/native-abi/PhotoCutoffProbe.c` runs the real native window and helpers (64 cases x 5 gates, RAX/source preservation, guards, 19 relay unwind starts, atomic restore/reinstall; three relay mutations are caught). v2 regression probes rebuilt against v3 and the 44-export proxy test pass (`work/cutoff-candidate-build-test.log`). Review: `work/photo-cutoff-actual-source-review.txt`.

Limitations: more lights now reach ranking; if retained lights hit 512 the secondary merge stops. GPU/cluster limits and performance are untested.

Build: `Build-CutoffCandidate.ps1`, then `work/write_cutoff_manifest.py`. Install (game closed): `Install-CutoffCandidate.ps1`. Rollback to lighting-v2: `Restore-LightingV2.ps1`.
