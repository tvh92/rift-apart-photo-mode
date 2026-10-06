# Photo Mode entry-fog candidate

The game uses different processed fog settings near the Corson V statue and at a distant Photo camera. Retaining the nearby numeric settings in a temporary live test restored the dark pit fog; merely increasing volumetric depth did not.

This candidate captures numeric fog settings on the first primary-view frame of each ordinary Photo session, after native regional processing. While the Ctrl details preference is enabled, it copies that snapshot into the current frame's renderer block before fog constants are prepared. Current camera position still drives height integration and projection. Ctrl off uses native fog; leaving Photo Mode discards the snapshot, and re-entry captures again.

It retains the existing Ctrl shortcut, geometry preference, camera speeds and no-clip. No indicator or skipintro. Ordinary light illumination is still unresolved. Fog changes normally associated with moving into another region are deliberately held during the enabled Photo preference.

The 132-byte copy covers renderer+110..193 and omits texture-dependent fields194..19B. Source atmosphere, texture/resource records, gameplay rendering and saves are untouched. The guarded callsite is RVA12BD0B0 on executable SHA25651299faca61866cf10ea9035a15b8f22600a56557dd5ffc1aad390d5a54e6d82. An aligned eight-byte CAS changes only the five-byte CALL, preserving its following TEST; thread coordination excludes execution inside that window. A leaf relay supplies the original primary-view pointer to the wrapper, which calls the original fog-preparation function exactly once. Shared callback slot65A3080 is untouched. Failure to publish the fog install leaves its wrapper transparent.

`Build-FogCandidate.ps1` builds only this separate directory and runs isolated relay/cache, Photo lifecycle/Ctrl, camera behavior, and HID forwarding/unsupported-process tests. `work/verify_fog_candidate.py` records source hashes, unchanged sources, matching dependency DLLs and validation. Build/test success is separate from the next real-game startup and Photo test.

`Install-FogCandidate.ps1` requires the game/Overstrike closed, the exact executable and validated DLL, and either the confirmed Ctrl DLL or this candidate. It backs up the confirmed Ctrl DLL, preserves the INI, runs the complete existing asset/intro/profile audit before and after installation, and rolls back a failed candidate installation when safe. `Restore-ConfirmedCtrl.ps1` restores that exact known DLL with the game closed. Production `outputs/camera-native` remains the user-confirmed baseline; do not run its binary-shortcut builder as a way to reproduce this candidate.

The user confirmed the native test works. Exact installed hash and runtime confirmation are recorded in build-verification.json; the confirmed source/DLL/log snapshot is under `outputs/confirmed-photo-fog/2026-10-05`. Original full movies remain installed. Preserve this working build while developing a separate lighting candidate.
