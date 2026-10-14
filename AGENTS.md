# Rift Apart Photo Mode research handoff

**Git migration,6 October2026:** private repository `https://github.com/tvh92/rift-apart-photo-mode`, branch `main`. The existing project directory is the local Git working copy; retain its layout. Read `README.md` for repository scope/dependencies and `migration/local-artifacts.json` for excluded local files. Source, our own proxy DLLs, rollback snapshots, tests, comparison reports and research notes are tracked; game assets, raw capture directories, tool downloads and caches remain intact locally. Migration does not change the installed game. Use repository-relative paths for new work; older absolute paths describe the original machine.

**Currently installed (6 October, later):** lighting-v3 DLL `c4be06b9e069829ba3c173ab3545353f38de04d6a98c5f58533af42ae9efbe66`, package `outputs/camera-native-lighting-v3`. Root cause of the bridge-lamp blips is identified: light filter job 0x10B9A50 drops lights with flag bit18 whose front-of-bounds distance exceeds rec+A0 (bridge lamps: 150) before upload (0x10B9C00/0x10B9C07); v2's fade bypass made that hard edge visible. v3 adds only PhotoCutoff.h (guarded aligned8 relay at 0x10B9C00) that skips this drop for the primary Photo view with Ctrl on; all v2 sources are byte-identical except PhotoLOD.h wiring/logging. Real-native probe, v2 regression probes, proxy test, independent review (`work/photo-cutoff-actual-source-review.txt`, no blockers) and full pre/post installation audits pass. **Runtime update, 6 October:** user reports lighting works fairly well, but distant flicker, poor Ctrl response and nearby lights disappearing with Ctrl OFF remain. Sargasso sky crash occurred with Ctrl ON; both recent dumps contain NRI D3D12 Map error 0x887A0005 and matching Windows driver-recovery events. The triggering renderer workload/path is unresolved. Current installed v3 is preserved; this investigation has made no game-file/settings/process changes. Tested source/DLL/feedback snapshot: `outputs/tested-photo-lighting-v3/2026-10-06`. Read `work/lighting-v3-runtime-followup.md`; no crash-height reproduction is requested.** Rollback: `outputs/camera-native-lighting-v3/Restore-LightingV2.ps1` (game closed). Evidence: `work/bridge-light-next-diagnostic.md`, `work/light-query-array-producer.md`. The v2 paragraph below is the previous state.

**Previously installed (6 October):** lighting-v2 DLL `16dcd44057c3114b123e25974b9b563afc487650686d3985784614caba5f7cbd`, package `outputs/camera-native-lighting-v2`. Extends the previous RGB far-fade override to ordinary specular bit20 and the separate type4 far fade. Ctrl still controls the Photo-only detail override, including the unchanged confirmed fog implementation and the fading ON/OFF notice. User explicitly waived a separate indicator test and requested continued lighting work; do not ask for that UI test. Local native/UI probes, actual-source review and full pre/post installation audits pass. User now confirms the notice works well, but lighting remains the same as before: no additional visible improvement from v2. Both lighting hooks installed and the shared relay counter291014 is logged; it does not distinguish hook types. Preserve source/DLL/log/feedback snapshot outputs/tested-photo-lighting-v2/2026-10-06. Remaining illumination cutoff is unresolved. Original movies, INI and assets are preserved. `Restore-PreviousStatus.ps1` returns to exact status770; its `Restore-TestedLighting.ps1` can then return to testedfa3. Use only the guarded package scripts with the game closed. Read-only bridge captures are complete; see the completed-capture note below. Keep installed v2 stable; remaining illumination cutoff is unresolved.

### Completed bridge cutoff captures, 6 October

The user supplied three stationary Ctrl-ON positions in PID9236: near, beyond the first visible cutoff, and back inside it. Capture paths and comparisons are retained in `work/bridge-light-near-far-comparison.json` and `work/bridge-light-cutoff-bracket.json`. Near: six accepted samples,91 pass67 records each. Far: six accepted samples,135 or141 records. Inside: two accepted samples,143 records each. A tentative six-light spatial group has radius25. Its z~42 pair is present in every near/inside sample and absent in every far sample; the other four retain exactly identical RGB across near/far. This supports pre-upload submission exclusion rather than another brightness-fade explanation, but position matching does not prove source identity or the precise gate. The closer/far center-distance bracket is about137..166 world units; it is not an exact LOD threshold. No process writes or installed-file changes were made.

Observer correction: passBB is a null-argument queue marker; the frame job is returned separately. The earlier passBB-param+18 query claim in the initial review is retracted. The far capture's one error per sample is the obsolete attempted passBB null read, not a failed pass67 record read. Raw captures are preserved. The current observer removes this path. Archive reserved capacity16384 is allowed while populated count remains bounded8192; unused capacity is not read.

Typed source-query observation remains unresolved. Callback12B8740 and manager674EC10 identify request slots; slot68 is the output array and slot70 the output-count pointer (slot50 is filter context). Deriving query from counter-10/-20 finds the primary owner, but the request output pointer differs from current query8/18. The observer refuses all such source-array reads rather than weakening identity guards. Latest metadata: `work/live-lights-readonly/20261005T231220416213Z-bridge-query-pointer-proof.json`, six accepted queue samples143 each, zero validated source queries, zero writes. These pointer candidates alone are not source captures. Eighteen isolated observer tests pass. Further work should trace query lifecycle/selection or prepare bounded in-process diagnostics with exact ABI/build guards. User was told they can close the game; do not require another live positioning session until a concrete diagnostic is ready. **Update:** the observer now validates request ownership by registry key (generation/index/bit) plus the query's stored key at +70/+68, and reports worker output separately from current query arrays; 28 isolated tests pass, no live run yet. See `work/bridge-light-next-diagnostic.md`.

**User-confirmed fog release:** DLL2286 `228620169d5741cd57d544047d351e7bd3c7df541778bc78c17ea0655bcb6f2a`, exact source/DLL snapshot `outputs/confirmed-photo-fog/2026-10-05`. Preserve it. Lightingfa3 result is partial: user thinks it works, but reports a farther light disappearance distance with Ctrl enabled. Real log confirms startup/Photo/Ctrl and867005 primary-light relay applications. Exact testedfa3 source/DLL/log snapshot: `outputs/tested-photo-lighting/2026-10-06`. Do not mark illumination completely fixed. Remaining ordinary-light exclusions are unresolved; focused trace `work/ordinary-light-pre-fade-exclusions-luna.txt`. Current lighting-v2 retains confirmed fog and the indicator, while extending the far-light fade bypass; see the current installed paragraph.


**Latest loading diagnostic resolved for current use:** original full movies load successfully with both the Ctrl5c baseline and the now-confirmed fog2286 build. Leave original movies installed. Skipintro is abandoned. Read `work/two-byte-ctrl-loading-diagnostic.md`, `outputs/startup-repair/current-intro-comparison.json` and `work/lighting-fog-current.md`.


Updated 6 October 2026. This file is the current handoff. Older reports describe earlier stages and may say a now-tested feature is untested. Distinguish user-confirmed runtime results, decoded asset facts, static disassembly, and hypotheses.

## User objectives and authorization

- Continue modifying the game's existing Photo Mode, especially its native Free camera.
- Completed: extend the camera tether from 10 to **1000** (finite, not mathematically unbounded), normal movement **10x**, held-Shift movement **100x**, automatic loading on ordinary game launch, persistence across leaving/re-entering Photo Mode, and permanent Overstrike asset installation.
- Completed collision update: user confirmed the requested no-clip/re-entry/speed test "Works flawlessly, nice job" on 4 October 2026. Preserve this behavior and its verified pre-LOD rollback DLL.
- User-confirmed fog DLL: `228620169d5741cd57d544047d351e7bd3c7df541778bc78c17ea0655bcb6f2a`. Exact source/DLL snapshot: `outputs/confirmed-photo-fog/2026-10-05`. Current installed lighting-v2 and partial lightingfa3 result are described at the top. It preserves all confirmed camera/assembly/geometry/forwarding/fog source files; only PhotoLOD integration/diagnostic logging and new PhotoLight.h differ. Ctrl5c baseline is also retained under `outputs/camera-native-fog-candidate/backup/2026-10-05-before-native-fog`.
- Earlier adjustable speed request is satisfied by held Shift; a slider was optional, not a remaining requirement. INI speeds currently load on startup. Hot reload or extra controls are optional improvements.
- Original research also discussed camera control outside Photo Mode/during cutscenes and broader freedom/streaming limitations. These are exploratory secondary topics, not an agreed gameplay-camera implementation. Do not silently expand the mod into gameplay changes.
- User explicitly revoked the original no-DLL constraint and approved native DLL installation and necessary runtime changes. Existing DLL is locally built from included source. Do not download/run unknown mod binaries.
- User requested **GPT-6 Luna subagents for gruntwork**. Delegate bounded independent read-only research when useful; keep risky edits and installation coordinated by the main agent.
- After a request to launch/test, user closes the game before replying. Verify processes locally; do not ask again unless the game is still running. Never reinstall after asking the user to launch: finish all file changes before the test request, and keep the game closed throughout installation.
- Do not modify saves. Preserve reversibility and exact executable-build checks. Ask for runtime testing only when a concrete candidate is ready.

## Workspace, runtime, and supported build

- Workspace: this repository root (moved from `C:\Users\Tim\Documents\Codex\2026-10-04\prompt-for-the-research-instance-research` on 2026-10-14; see `MOVE-NOTE.md`).
- Game: `C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart`.
- Python: `C:\Users\Tim\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.
- Steam app 1895880; inspected build **23987138**; depot 1895881 manifest **2186341403927512776**. These identify the supported local build, not a claim about the newest release.
- `RiftApart.exe` SHA256: `51299faca61866cf10ea9035a15b8f22600a56557dd5ffc1aad390d5a54e6d82`.
- Pristine TOC: `outputs/startup-repair/toc.steam-original`, 12,574,728 bytes, SHA1 `64946f571579d9ea0a17e675682e2994dc0f20fc`.
- Current game `toc.BAK` matches that pristine TOC. Never treat a historical migration backup as vanilla; several early backups were contaminated by mods.
- Base `d/config` is vanilla, SHA256 `f659e13afe36c335d3ab54441898378164a51c2c469a1a368a51c8a005310bb3`. Original base movie assets are restored/unchanged.
- Official portable Zig 0.15.2 compiler remains in `work/toolchain/zig-x86_64-windows-0.15.2/`; checksum was checked against official download index. Native build script uses `work/zig-cache`.
- `work/disasm/iced_x86` may require an escalated read-only command due to local ACLs. Avoid recursive searches of compiler/cache trees and printing large LOD traces or binary files.

## Engine and approach distinctions

Insomniac proprietary engine with Nixxes PC integration, not Unreal. Public reverse-engineering references are Rivet (schemas/formats), ALERT (DSAR/DAT1), Overstrike (asset replacement), and rivet_hook (runtime loader/camera examples). Public schemas are useful evidence but do not prove an active PC renderer path.

- Config/asset Stage mods are file-based overrides and do not themselves inject code.
- Overstrike is an external installer which rewrites the index and emits replacement archives. Asset installation does not require attaching to a running game. Its script/loader path is different.
- ReShade add-ons and native plugins execute code in the game process, normally via a proxy/injected DLL or loader; they are not purely file-based asset edits.
- The historical Python camera helper was an external process reading/writing game memory: no injected DLL, but still process tampering. It is superseded and archived. Never run it alongside the native DLL.
- The installed `hid.dll` is a proxy loaded by the game, executes in process, and changes native vtable pointers. It is a runtime modification; being loaded at startup does not make it an asset-only mod.

## Confirmed asset findings and installed override

Photo Mode configuration asset ID **AED6101948AAFA54**, type `PhotomodeSystemConfig`:

- Original `d/config` decompressed offset 10,830,144, length 263,280 bytes.
- Original TOC asset index 65,761 (zero-based); separate header offset 2,351,412.
- TOC outer magic `34E89035`, inner DAT1; `d/config` is DSAR version `00010003`, compression type 3 (LZ4).
- Authored native Free camera uses `PhotomodeCameraFreeMovePrius`, original tether 10, movement 2, rise 1.
- Installed path: `.Cameras.Cameras[1].CameraType.Obj.CamData`: tether 1000, movement 20, rise 10, acceleration 10000. Root `FreeMove.TetherDistance` remains 10; Light Mode tether remains 15.
- Other original limits: light orbit max distance 8, minimum height -7, maximum height 7. Light placement and camera tether are separate controls.
- Original numeric fields were packed integers; the same-size patch widened tether, move, and rise values within existing aligned padding. Preserve serialized sizes/types and validate decoded before/after differences, not just raw byte searches.
- Stage V2 package `outputs/camera-controls/PhotoMode-10x-Tether1000.stage` preserves the original TOC header; raw payload SHA256 `7e1538b0742262daec41965bdce20d4a0252502a2eded61c87d97fe56373d7c5`.
- Current installed archive is `d/mods/mod1`; original `d/config` remains vanilla. Last asset override wins if another mod changes the same asset.

Read/prepare tools: `work/inspect_photo_config.py`, `work/prepare_tether_patch.py`, `work/prepare_camera_speeds.py`, `work/package_camera_stage.py`. Some are historical one-shot scripts with pre-migration hash/index assumptions: inspect before running. The parser may execute reads/output generation at module level; use AST-extracted functions when avoiding side effects. `outputs/photo-mode-tether-1000` and `outputs/camera-controls/backup`, `presets`, `change.json` remain because they provide original/reproducible asset inputs. Direct base presets have lower priority than the active Stage override.

## Confirmed native camera layout and implementation

All addresses below are **RVAs for the exact executable hash**, never portable absolute addresses.

| Object/path | RVA/offset | Evidence/meaning |
|---|---|---|
| Free camera vtable | `0x45FD8B0` | slot 12 original method `0x1A5D4D0` |
| MotionFly vtable | `0x45FDEF0` | slot 10 original update `0x1A5EBA0` |
| Free source data | `+F8/+FC/+100/+104` | tether/move/rise/acceleration |
| Motion controller | `+68/+6C/+84/+70` | tether/move/rise/acceleration |
| Free entity identity | `+1C` | matched to motion owner `+44` |
| Tether helper | `0x183E5D0` | writes motion `+68`, related validity flag `+95` |

Free activation/setup copies source camera data into a matching runtime motion controller. Editing source data alone failed in early live tests because motion values were cached and instances were recreated. The active movement-update path reads the controller fields. Successful external helper independently read back both source and controller values; then the native implementation replaced that helper.

Native sources/artifacts: `outputs/camera-native/CameraBoost.c`, `CameraStubs.S`, `HidExports.c`, `hid.def`, `export-manifest.json`, `Build-NativeBoost.ps1`, install/uninstall scripts, `hid.dll`, and README. Keep these and useful `work/native-abi` test source plus `work/test_native_proxy.py` for future native changes.

- HID proxy forwards all 44 exports of this machine's Windows HID library to System32. Worker starts on the first HID call outside DllMain, verifies the full EXE hash, checks original targets, and pins the module.
- Free hook captures owner identity. Motion hook checks identity/type and writes on the game's update thread. No heap scan, no save writes, no TOC reads/writes.
- Current `PhotoModeCamera.ini`: `Normal=10`, `Boost=100`, `Tether=1000`. Focused-game Shift selects boost; release restores normal. Ctrl+Alt+F10 disables runtime boost until next launch and restores captured controller baseline.
- Another mod using `hid.dll` conflicts. Unsupported EXE keeps forwarding but refuses hooks. Installer refuses unknown DLL replacement.
- Confirmed pre-LOD no-clip DLL SHA256: `ccbcdaeacb5525e05a68ede9924164f07f5d3c93e1ed6e189168bbfd8f9c8ff3`. The prior user-confirmed speed-only DLL (`97b9a29eed154973fb587e0fae965c441b9956096211523aa1f99ef1d6d03e81`) is preserved in `outputs/camera-native/backup/2026-10-04-before-collision/hid.dll` with source/manifests. `Restore-ConfirmedSpeedDLL.ps1` restores it with the game closed and refuses unknown EXE/DLL hashes.
- Isolated native tests checked forwarding, unsupported process refusal, ABI, owner filtering, normal/boost/release, baseline restore and replacement identity. User confirmed both speeds after re-entering Photo Mode and again with final short intro setup on the prior DLL. Rebuilt behavior/proxy/collision probes pass. User then confirmed the no-clip/re-entry/speed test on the current DLL: "Works flawlessly, nice job."
- Native speed owner matching is not yet a proven complete Photo Mode lifecycle detector suitable for global renderer overrides.

## Collision / no-clip: user-confirmed working

- Original camera could not pass through objects. The installed guarded collision-response bypass is now user-confirmed working. No Overstrike reinstall or asset/profile/TOC changes were made. Post-install audit and user confirmation: `outputs/camera-native/collision-candidate-installation-audit.json`.
- Schema `work/PhotomodeSystemConfig.cs`: `CamCollisRad`, field hash `0x3B89FD7D`, default **0.20**. Radius zero is an untested experiment, not an established collision-off flag; a zero-radius raycast could still collide.
- Determine whether this field is present in decoded config, where it is consumed, and whether movement collision is independent of intersection fade/visibility logic. Tether, world streaming, far clip and collisions are different constraints.
- Actual blocking path: `Camera2::PhotomodeCameraMotionFly::UpdateMiddle(float)` `[0x1A5EBA0,0x1A5F364)` builds a type-3 query through `0x118F070`, queries old/new positions through `0x11B9C30` (thunk to `0x11AA050`), then corrects the candidate position on a hit. Original bytes at `0x1A5F1E7`: `E8 44 AA 75 FF 84 C0 74 3B`. Candidate changes only branch `0x1A5F1EE` from `74` to `EB`, skipping hit correction while retaining query/cleanup and later tether/calculations. The executable file stays unchanged. Static references point to the Photo-specific motion vtable plus one dispatcher, with no non-Photo caller found.
- `NoClip=1` defaults on even when absent from the existing INI. `NoClip=0` at startup retains native collision. Ctrl+Alt+F10 in the matched Free camera restores the original branch along with speed baseline. Exact EXE hash and nine-byte window guards, byte CAS, original page protection and instruction-cache flush are retained. Failure/conflict leaves speed hooks available.
- Isolated `CollisionProbe` checked exact-window refusal, one changed byte, unchanged surrounding bytes, page protection, symmetric restore and changed-byte conflict refusal. Rebuilt `BehaviorProbe` checked speed behavior and hotkey collision restore. Camera ABI assembly is unchanged. User's requested wall/solid-object, Photo Mode re-entry and speed test is confirmed working; the disable hotkey was verified in isolated tests, not separately claimed as user-tested.
- A method clone was rejected during design because original unwind metadata uses `__CxxFrameHandler4` with FuncInfo4 data; copying code/RIP displacements alone would not preserve exception cleanup. Evidence: `work/collision-continuation-luna-report.md`. CamCollisRad's specific consumer is still unresolved; zero radius was not installed or claimed effective.

## LOD: two-byte Ctrl shortcut; lighting/fog next

Current installed candidate is the entry-fog2286 DLL described at the top. The following Ctrl implementation records the user-confirmed baseline5c; production `outputs/camera-native` still holds that baseline. Reproduce the current candidate with `outputs/camera-native-fog-candidate/Build-FogCandidate.ps1`, not the baseline binary-shortcut builder.

The rebuilt Ctrl-only candidate8cd also stalled loading. Eager06ce and lazy7d indicator candidates failed before it; the exact7508 geometry DLL starts successfully. The cause remains unproven. All three failed DLLs and logs are preserved. The user requested abandoning the indicator and focusing on lighting/fog.

The current candidate changes exactly two bytes in the user-confirmed7508 DLL: file0x23F3 (VK_MENU12 to VK_CONTROL11) and0x2403 (L4C to VK_CONTROL11). Every other byte, including imports, layout, relocations, exports and unwind metadata, is identical. No relinking. The three original key probes now check Ctrl. Tapping Ctrl toggles on the rising edge in focused active Photo state4; holding does not repeat. Original lifecycle/focus checks, geometry, speed, no-clip and disable restoration remain. There is no indicator.

Reproduce with `Build-NativeBoost.ps1` (default guarded binary patch via `work/patch_working_dll_shortcut.py`). `-ExperimentalRecompile` is an explicitly experimental compiler route, not validated for startup. Source reflects the same key expression; the original PDB/import library remain valid. Do not casually recompile/reinstall the production DLL.

Verification: `work/binary-ctrl-shortcut-verification.json` proves the exact two-byte difference; `work/test_binary_ctrl_shortcut.py` executes the actual patched DLL hook in an isolated non-game process, testing rising edge/held suppression, exact key probes, focus/startup gates and original callback. Native lifecycle probe and HID forwarding/unsupported-process guard pass. Full installed audit: `outputs/camera-native/binary-ctrl-installation-audit.json`. INI, executable, four asset overrides, profiles/libraries, pristine TOC backup, base config and movie bytes remain unchanged. No game installation changes after requesting the next launch test.

Lighting/fog research continues without an installed speculative patch. Do not revive indicator work without user steering.

Historical indicator candidates follow:

**Latest installed DLL SHA256:7d4234168e04020b65bd2af2a88314bffe9bef2baadeb2994c2901b539008665**. User confirmed the7508 rollback works. The new candidate removes StartPhotoIndicator from prepare_photo_geometry; only a validated state4 notice can start the UI after checking visible focused same-process HWND. Show/Hide/F10 only queue notices and cannot start the worker. CAS prevents duplicate starts; failure/exit resets the guard for future Photo entry/toggle. Geometry/camera/collision hooks remain unchanged. Tests cover no startup thread in14/10/11/0/1/2, one active worker, Ctrl/chord/focus behavior, fade/cleanup/restart, speed/no-clip/disable behavior, card rendering and HID forwarding. Independent review found no blocker. Artifacts: `work/lazy-indicator-validation.json`, `work/lazy-indicator-current.md`, `outputs/camera-native/lazy-indicator-installation-audit.json`. Startup regression mechanism remains unproven; new runtime test pending. Finish all file changes before launch request; no reinstall after it.

The following records the prior failure/rollback and withdrawn eager candidate:

**Current installed DLL SHA256:7508bd33654d057202fbd91b8c81d8622dca1c1e781c21b52ce82023fa14b272**. The user could not test the Ctrl/indicator because the game became stuck loading. With the game closed, the guarded previous-DLL rollback completed and the complete file audit passed. Saved failure log stops at Photo states14/10/11, preference native, before any shown indicator. Root cause is unproven. Read `work/control-indicator-loading-failure.md` and `outputs/camera-native/control-indicator-loading-rollback-audit.json`. The current request is a baseline launch of the restored build, not an indicator test. Do not reinstall after requesting launch. The newer candidate remains preserved but its manifest blocks reinstalling unchanged.

The following paragraph describes the withdrawn control candidate and its earlier isolated tests, not the installed runtime state:

**Current installed DLL SHA256: 06ce078afaca25aeb95cca6da595ea8f8b54f8a9ccac3aef833c64fadb6a6de8**. Read `work/lod-candidate-current.md` first. The geometry implementation is unchanged from `7508bd33654d057202fbd91b8c81d8622dca1c1e781c21b52ce82023fa14b272`, which visibly toggled distant exhausts, objects, walls, pipes, foliage and environment details in the user's test. Ctrl alone now toggles on release in focused active state4; modifier chords/focus loss cancel. `PhotoIndicator.h` adds a click-through/nonactivating native card holding900ms/fading700ms. Ctrl+Alt+F10 retains restoration. Photo states1,2,4 gate geometry; special unproven states retain native LOD. Isolated controls/indicator/ABI/collision/proxy checks and complete installation audit pass; **new Ctrl/indicator in-game test pending**. No asset/intro/profile/TOC/INI changes. Previous geometry package retained in `backup/2026-10-05-before-control-indicator/`; `Restore-PreviousLODDLL.ps1` restores it.

User lighting symptom: lights stop illuminating nearby surfaces as the camera moves away. Fog symptom: dark fog in bottomless pits turns bright white. Reproduction: Corson V, Nefarious City near the giant golden Emperor Nefarious statue. Screenshot `work/corson-v-white-fog-user-screenshot.png` shows broad pale bands between/behind buildings below the purple sky. Neither lighting nor fog is fixed in this DLL. `work/lighting-effects-lightcull.md`, `lighting-effects-runtime-continuation.md`, and `pc-lod-continuation-luna-world-light-consumer.txt` document schema candidates and unresolved native consumers. Do not conflate vehicle-only light distance, Photo-added light range, shadow LOD, or generic DDL atmosphere blending with a proven world-light/fog control.

Scene-specific fog archive inventory: `work/corson-v-atmosphere-asset-index.md`,95 entries in `d/atmosphere`, custom built-file type21D5E72C; generic config parser cannot decode those settings. Nefarious hits are sky-texture paths only, not a proven active scene atmosphere. Native reflection offsets do not map directly to built-file bytes. `LevelLightManager` RTTI methods traced in `work/pc-lod-continuation-luna-light-rtti-consumer.txt` expose descriptor handling/cleanup, not a world-light distance predicate. Next work needs a built-atmosphere decoder/scene binding or a proven live renderer block, and actual light submission/camera-origin evidence. New UI limitation/review record: `work/control-indicator-review.md`.

The prior investigations below explain rejected global/view alternatives; the installed candidate avoids them. Do not equate increasing camera range or graphics preset with removing model/texture LOD, nor promise highest detail for unloaded objects.

- `work/lod-resume-notes.txt` is the compact checkpoint; keep all `work/lod*`, `work/lod_pc_trace`, `work/lod_perf_action`, graphics tracing scripts, schemas, `perf_spec.json`, and RIP/branch indexes.
- `PerfSpecConfig` asset had PS5-labelled rows. PC applicability unproven.
- `PerfSpecData +0xC` is a **probable** LodScaleMultiplier (default 1), `+0x10` a **probable** ModelLodClamp (default LOD0). Located reflection metadata, not an actual renderer consumer.
- `CamLodScale` belongs to `CameraEngineItem` editor metadata; applicability to the native Photo camera is unproven. Global LOD help text found so far applies to a cinematic track, not a demonstrated generic override.
- PC graphics validator RVA `0x168AD40`, NxAppImpl vtable `0x456C0D8` slot `+158`, validates/stores LOD enum `+70`, maximum 5. It is validation only. NxSettingsImpl preset copy row `+B8` to graphics output `+70` is not the renderer selection path.
- Adjacent callbacks `0x168A3E0/0x1689E50/0x168A3F0` store NxApp callbacks `+A48/+A50/+A58`; renderer consumer remains unidentified.
- Photo system main vtable `0x2FBF630`, shared vtable `0x45FD1E0`. Shared `+54` is setup flag; `+50` varies 0..14, 14 closed/default. Status routines `0x1A57320/0x1A57340`; start `0x1A56D70` saves globals/filters; stop `0x1A57560` restores. Validate lifecycle semantics before writing globals.
- `work/rip-refs.bin`, `work/branch-refs.bin`: sorted `<III>` tuples of target RVA, instruction RVA, length. These reusable indexes avoid repeated whole-EXE decoding.
- New continuation established an actual **geometry** consumer: tier selectors `0x111A700` and `0x111A910` compare distance against five model thresholds `+58/+5C/+60/+64/+68` scaled by `0x111EB10`, then retain object/per-view clamp logic. Initial distance tier is **0..5** before masks/clamps. Callers `0x111F86C`, `0x111FF30`, `0x1121EA4` use the result to index model variant/resource tables. This is separate from boolean size/visibility helper `0x111AD50`.
- Scale source in geometry callers is `[view+1D18]*[view+1D14]` times model bounds. `+1D14` has a projection/camera setup writer `0x1237399` in `0x12372F0`. `+1D18` writers include cinematic/input records and copies around `0x1A814DC/0x1A82B00`; their exact active-view identity remains unproven. Global scale `0x5339184` (alternate `0x5339188`) participates in both geometry thresholds and size/visibility helpers, so changing it indiscriminately could also change culling. Do not install it as a geometry-only override.
- Focused evidence: `work/pc-lod-continuation-luna-geometry.txt`, `work/pc-lod-continuation-luna-view-field-trace.txt`, `work/lod-candidate-functions.txt`, `work/lod-geometry-selection-continuation.txt`, `work/lod-model-globals-continuation.txt`. `0x53391E0/F0` candidates traced into `0x108E8B3..0x109415E` remain unnamed and must not be labelled generic geometry LOD from a max-six count alone. Exact PC UI LOD getter/setter `0x16A1350/0x16A86A0` only access settings struct `+70`; no renderer bridge found.
- The exact view alias remains unproven. The installed geometry-only candidate avoids changing any view/global LOD scale, using the verified Photo callback lifecycle instead. Next step is the user comparison/re-entry/gameplay test; expand special Photo states only after proving their semantics. Native available-variant floor details are in `work/pc-lod-continuation-luna-tier-floor.txt`.
- Separately test model geometry, texture mip residency, vegetation, shadows, streaming/culling and far clipping. Highest-detail forcing can increase VRAM/CPU/GPU cost and stalls; rendering overrides cannot create missing streamed content. Measure scene changes and performance rather than claim complete LOD removal from a changed field alone.

## Photo Mode defaults / vignette: new unresolved request

User wants options such as vignette to start at zero rather than the game's default. Keep in-game sliders usable. Do not indiscriminately zero FOV, exposure, aperture, focus distances, or other parameters where zero is invalid/non-neutral.

- UI config asset **8E1F557CB712559F**; decoded instance `work/config_00af8d54.json`; Photo system decoded instance `work/config_00a54140.json`.
- `work/UIPhotoModeConfig.cs`, `UIPhotoModeOption.cs`, `PhotoOptionIds.cs` describe options. UI supports FOV, exposure, DOF, color blend, vignette intensity/center clear, film grain, sharpening and other controls.
- UI option schema has `ValueMin`, `ValueMax`, `Fidelity`, `FastFidelity`, slider/clamp type and setting strings, **no per-option default field**. Changing slider limits does not establish a startup default.
- Decoded limits include vignette intensity max 10 (implicit min 0), exposure -4..4, FOV .35..2 radians, DOF focus distance 1..180. These are bounds, not measured starting values.
- Trace native initialization/reset and any remembered per-session/user settings. Determine whether initial effect values can be supplied by asset data or need a one-time lifecycle hook. Apply neutral defaults when entering/resetting, not continuously overriding manual slider edits.
- Continuation traced shared getters `0x1A57E80/D70/D40/EB0/DD0/DA0` to renderer blocks `+A8/+F8/+300/+524/+3EC/+4C0` via `0xFB1130` (fallback `0xFAE1A0`). Entry/reset snapshots copy these blocks into Photo fields; exit `0x1A57560` also restores `Photo+70/+74` to renderer `+388/+38C`, `+68/+6C` to `+3D8/+3DC`, and other snapshots. This establishes preservation, not identified vignette/grain controls.
- Fresh effects evidence `work/effects-continuation-luna-reflection-trace6.md` identifies named DDL vignette/grain fields, but their Photo/renderer binding is still unproven. `effects-continuation-luna-dispatch-trace5.md` explicitly retracts a provisional numeric-ID mistake: Photo +50 is lifecycle state, not PhotoOptionIds. Neutral effects remain unmodified.
- UI RTTI recovered: `UIPhotoModeOption` vtable `0x3145830`, `ScreenUIElementPhotoModeOptions@GUI2` `0x2F13150`, `UIPhotoModeOptionsPage` `0x31458A0`, `UIPhotoModeConfig` `0x31459F0`. Method `0x170D280` stages groups/list values; it did not establish numeric option-ID to renderer setter mapping. No neutral defaults are installed. Preserve `work/effects-continuation-luna*.md`, helper and `work/effects-*-continuation.txt`; do not zero unlabeled snapshot blocks.
- Native Photo option enum does not expose MoveSpeed/RiseSpeed. Built-in `kCameraFast / FPS Cam Speed Up` strings exist, Photo Mode binding unconfirmed. A new slider would need native binding beyond adding UI data.

## Permanent installation and historical skipintro experiment

Skipintro was later abandoned by the user after a loading regression. Original full movies are currently installed and user-confirmed. The two-second package and profile listing below describe a historical state; do not restore them. Current profiles have `NoIntro.stage` disabled and `PhotoMode-10x-Tether1000.stage` enabled.

Historical Overstrike profile listing (superseded):

1. `NoIntro.stage`: disabled.
2. `NoIntro-Fixed-2Seconds.stage`: enabled (`d/mods/mod0`).
3. `PhotoMode-10x-Tether1000.stage`: enabled (`d/mods/mod1`).

Copies: `outputs/Overstrike/Overstrike.exe` and `C:\Users\Tim\Documents\Bestanden\Downloads\Overstrike 1 1.8.1 2026-09-04T22-57Z vzbjnz4Zh\Overstrike.exe`. Version 1.8.1, same SHA256 `352be024109c81604d2e1109adb29bab5493f0290779fc296e0c75f61dfa5565`. Run each from its own directory (profiles/library depend on cwd). RCRA scripts settings remain disabled; the HID proxy loads separately.

- Fixed intro package `outputs/startup-repair/NoIntro-Fixed-2Seconds.stage`, SHA256 `5fc62afad01e5be5c66bfd92921f41bc9a9fe301bb50e22f27e48024516b74cd`. It uses first 60 original frames at 30 fps, preserves original codec flags/audio tracks, pads each replacement to original asset length. Original base movie archive is unchanged.
- Unchanged original videos routed through Overstrike loaded successfully. Four-frame clips failed; two-second clips succeeded using the exact same index layout. This points to playback-length-sensitive startup behavior for tested clips, not proven general TOC serialization corruption. Exact minimum duration/internal cause is unknown.
- Separate real risk: Overstrike reuses `toc.BAK` if present and creates it from current `toc` if absent. Never delete BAK while TOC is modded; after updates establish a Steam-verified clean baseline first.
- Current maintenance: `outputs/camera-controls/Assert-CleanBaseline.ps1`, `Check-Installation.py`, `Reinstall-Camera.ps1`. The audit supports only the exact current camera-only/camera+fixed-intro payloads; new mods require deliberate audit updates. It compares both libraries/profiles, all 340,662 asset records, original archive prefix, other DAT1 sections, base assets, EXE and DLL.
- Check-Installation.py writes its report and overwrites user-confirmation additions; it does not change game files. Reinstall is a mutation, not a read-only check. It snapshots current audited state and rolls back from that, not contaminated historical backups. Keep game closed for the entire operation.

## Archive and retained evidence

Finished startup experiments, offline test installs, old startup packages, historical backup snapshots, legacy Python helper/launchers and transient live logs were moved to `archive/2026-10-04-completed/`, preserving original relative layout. Mapping is in `manifest.json`; no game/manager files were moved. Archived scripts may contain stale absolute paths and are evidence, not active installers. Backups remain recoverable but are not necessarily pristine.

Active camera/LOD research, generated schemas, source, current installers/auditors, toolchain, asset inputs, current packages, pristine TOC and final success records remain in place. `outputs/read-only-findings.md` is historical discovery, superseded for current runtime/install status.

## Primary references

- Rivet schemas: https://github.com/neptuwunium/rivet/tree/a631c96ed6455f9873a646825d37883f99defa6e/Rivet.DDL.RCRA
- Free data: https://github.com/neptuwunium/rivet/blob/a631c96ed6455f9873a646825d37883f99defa6e/Rivet.DDL.RCRA/Types/FreeMoveCamData.cs
- Photo system: https://github.com/neptuwunium/rivet/blob/a631c96ed6455f9873a646825d37883f99defa6e/Rivet.DDL.RCRA/Types/PhotomodeSystemConfig.cs
- Photo option IDs: https://github.com/neptuwunium/rivet/blob/a631c96ed6455f9873a646825d37883f99defa6e/Rivet.DDL.RCRA/Enums/x4f56b709.cs
- ALERT DSAR: https://github.com/Tkachov/ALERT/blob/bc90ed9b53fbcaa3b7acf94b36f00e77eab0dacb/dsar_codec.py
- ALERT DAT1: https://github.com/Tkachov/ALERT/blob/bc90ed9b53fbcaa3b7acf94b36f00e77eab0dacb/dat1lib/types/dat1.py
- Overstrike RCRA: https://github.com/Tkachov/Overstrike/blob/OS/v1.8.1/Overstrike/Games/GameRCRA.cs
- Stage installer: https://github.com/Tkachov/Overstrike/blob/OS/v1.8.1/Overstrike/Installers/StageInstaller.cs
- Backup behavior: https://github.com/Tkachov/Overstrike/blob/main/Overstrike/MetaInstallers/MetaInstaller_I29.cs
- Runtime loader examples: https://github.com/neptuwunium/rivet_hook
- Windows x64 ABI: https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention

Use current primary sources and reproducible local evidence when investigating new behavior. Existing build-specific findings must be revalidated after any game update. Report implemented and user-tested results separately from candidates.
