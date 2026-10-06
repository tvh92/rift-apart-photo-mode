**Superseded:** rebuilt Ctrl-only8cd also stalled. Current installed candidate is the two-byte Ctrl patch `5c36943c6dfb45713382bf471e6f9939f857ee94f7789b8fefb2fc3abc292842`; read [binary-ctrl-current.md](binary-ctrl-current.md). Runtime confirmation pending. The rest of this document is historical.

# Ctrl-only Photo Mode build — 5 October 2026

Installed DLL SHA256: `8cd2d7f9dc5f549f7198b5685a151f3ca8e4075557da4af5424d2069ab48953f`.

User reported both eager06ce and lazy7d indicator builds stall loading. The7508 rollback is user-confirmed to start. User now directs: ignore the indicator, keep the shorter shortcut and focus on lighting/fog.

Production sources were restored from `backup/2026-10-05-before-control-indicator/` (7508), with only Ctrl tap/release and modifier/focus/state cancellation added to PhotoLOD. CameraBoost, GeometryLOD, ASM, HID and build script match the working baseline. No indicator source is included or present in the active source root; no GDI32 linkage or new window/worker/message code. Independent PE review confirms the exact same imported DLLs/APIs and unwind row count as7508. This does not prove the earlier stalls' exact cause, but removes the entire abandoned feature and dependency changes.

Ctrl toggles on release in focused ordinary active Photo state4. Holding does not repeat. Alt/Shift/Win/F10, focus or state loss cancel the press. GeometryLOD defaults on and retains native masks/resource floors. Speed/no-clip and Ctrl+Alt+F10 restoration remain unchanged.

Tests: `work/ctrl-only-validation.json` covers lifecycle/close/metadata guards, Ctrl tap/chord/focus, speeds/baseline/owner/no-clip/disable behavior and HID proxy forwarding/unsupported-process refusal. Full file audit `outputs/camera-native/ctrl-only-installation-audit.json` verifies current DLL, EXE, unchanged INI, same four asset overrides, matching profiles/libraries, pristine TOC backup, vanilla base config and original movie bytes. Current startup/shortcut runtime confirmation pending. Previous7508 rollback available with game closed. Do not reinstall after requesting launch.

The second failed candidate/log are preserved in `backup/2026-10-05-failed-lazy-indicator/` and `work/lazy-indicator-loading-failure-2026-10-05.log`. Eager failure is also preserved. Indicator work is abandoned per user; do not spend another iteration on it.

Lighting/fog reproduction: Corson V, Nefarious City near golden Emperor statue, saved screenshot in `work/corson-v-white-fog-user-screenshot.png`. Current lighting/fog research now has concrete built-atmosphere loaderFAE710 (custom type21D5E72C/base section02F06D4E) and generic LightDef distance-fade metadata. Actual renderer consumer/field mapping and active scene data must be proven before changes. Read `work/built-atmosphere-native-loader.md` and `work/pc-lod-continuation-luna-lightdef-distance-metadata.txt`. These paths remain unpatched in this build.
