# Current binary Ctrl shortcut — 5 October 2026

**Current confirmed state:** original intro movies reach the menu and Ctrl toggles details onDLL5c. User has abandoned skipintro experiments; leave original movies installed. No indicator. Lighting/fog remain outstanding; read `work/fog-renderer-parameter-copy-main.md` for the proven renderer fog bridge. Do not reinstall/recompile the working DLL casually.


**Latest loading diagnostic:** two-byte Ctrl5c also stalls after publisher logo with the two-second intro. Original full movies are now temporarily restored; same Ctrl DLL, camera, speed/no-clip and INI. Full audit passes; this original-intro comparison awaits user launch. Read `work/two-byte-ctrl-loading-diagnostic.md` and `outputs/startup-repair/current-intro-comparison.json`. Older runtime-pending and permanent-intro notes below are historical.


Installed DLL SHA256: `5c36943c6dfb45713382bf471e6f9939f857ee94f7789b8fefb2fc3abc292842`. Runtime confirmation pending.

The rebuilt Ctrl-only candidate8cd also stalled loading. Eager06ce and lazy7d indicator candidates failed before it; the exact7508 geometry DLL starts successfully. The cause remains unproven. All three failed DLLs and logs are preserved. The user requested abandoning the indicator and focusing on lighting/fog.

The current candidate changes exactly two bytes in the user-confirmed7508 DLL: file0x23F3 (VK_MENU12 to VK_CONTROL11) and0x2403 (L4C to VK_CONTROL11). Every other byte, including imports, layout, relocations, exports and unwind metadata, is identical. No relinking. The three original key probes now check Ctrl. Tapping Ctrl toggles on the rising edge in focused active Photo state4; holding does not repeat. Original lifecycle/focus checks, geometry, speed, no-clip and disable restoration remain. There is no indicator.

Reproduce with `Build-NativeBoost.ps1` (default guarded binary patch via `work/patch_working_dll_shortcut.py`). `-ExperimentalRecompile` is an explicitly experimental compiler route, not validated for startup. Source reflects the same key expression; the original PDB/import library remain valid. Do not casually recompile/reinstall the production DLL.

Verification: `work/binary-ctrl-shortcut-verification.json` proves the exact two-byte difference; `work/test_binary_ctrl_shortcut.py` executes the actual patched DLL hook in an isolated non-game process, testing rising edge/held suppression, exact key probes, focus/startup gates and original callback. Native lifecycle probe and HID forwarding/unsupported-process guard pass. Full installed audit: `outputs/camera-native/binary-ctrl-installation-audit.json`. INI, executable, four asset overrides, profiles/libraries, pristine TOC backup, base config and movie bytes remain unchanged. No game installation changes after requesting the next launch test.

Lighting/fog remain unpatched. Reproduction: Corson V, Nefarious City near golden Emperor statue; `work/corson-v-white-fog-user-screenshot.png`. LightDef fade-out metadata and native constructors establish a70-unit default and field+22C, but an actual renderer consumer is still needed. Built atmosphere parserFAE710 materializes the current atmosphere at registry52DDA20 slot+1C8. Runtime+478/+490 are named Fog map texture references. Unnamed scalar copies are not evidence of fog semantics; do not patch guessed offsets. Relevant reports: `work/pc-lod-continuation-luna-lightdef-distance-metadata.txt`, `work/built-atmosphere-native-loader.md`, `work/active-atmosphere-fog-block-trace.md` and `work/active-atmosphere-fog-consumer-trace.md`.
