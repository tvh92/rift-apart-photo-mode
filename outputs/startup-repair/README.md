**Current 5 October:** original full intros are installed and user-confirmed to reach the menu with working CtrlDLL5c. The two-second setup stalled after publisher logo with the same DLL. User abandoned skipintro work; do not re-enable or continue experiments. Older working-two-second notes below are historical. See `current-intro-comparison.json`.

Completed startup research. Historical diagnostic packages, logs and backups referenced below have moved to ../../archive/2026-10-04-completed/outputs/startup-repair/. Consult its manifest.json mapping. Current package, clean TOC, final installation records and maintenance inputs remain here. See ../../AGENTS.md for the current handoff.

# Startup repair and current diagnostic

## Current permanent installation

The working two-second intro is now packaged as `NoIntro-Fixed-2Seconds.stage` and enabled in both ordinary Overstrike profiles alongside the camera mod. Legacy NoIntro is disabled. The user confirmed that the two-second payload reaches the menu; the user also confirmed the permanent combined setup reaches the menu and both normal and Shift camera speeds work. Installed payloads, clean backup, all other asset records/sections, and unchanged camera DLL passed the file audit. See `NoIntro-Fixed-2Seconds.README.md`.

The key controlled comparison used identical TOCs: original full videos reached the menu; first four original frames (0.13 seconds) black-screened; first 60 original frames (2 seconds) reached the menu. This supports length-sensitive startup playback; a precise minimum or internal race is not established. This evidence supersedes treating the mod's video redirection or current clean backup as generally broken.

## Latest state after the user's Steam reset

Steam verification restored the pristine index; `toc.BAK` was absent. The native camera DLL remained. The asset camera stage was no longer active in the index. The previous camera-only audit is a historical result, not the state after this reset.

The original-video routing diagnostic was installed through a separate `routing-launch-original` profile. It routed unchanged original intro bytes through Overstrike, with TOC SHA-1 `78ee66e82f32eedf237490a7239c8d7f7760ebff` and a freshly verified pristine `toc.BAK`. The user confirmed it reached the menu. See `../../work/overstrike-audit/README.md` for the isolated five-case audit and comparable short-clip tests.

## Failed test: direct movie archive replacement (restored)

The diagnostic installed the original NoIntro clip directly at each of the three original boot-video offsets in `d/movie`. It replaces exactly 10,468 bytes per movie (31,404 bytes total), retaining the archive's size, original asset offsets, and all following bytes. The Bink header/index declares its four-frame clip length. `toc` and `toc.BAK` remain byte-identical to the working camera-only setup. NoIntro remains disabled in both Overstrike profiles; the camera mod remains enabled.

This tests whether redirecting boot videos into Overstrike's mod archives causes the stall. It is a diagnostic hypothesis, not a confirmed cause. The padded replacement decoded all four frames with the game's installed Bink runtime and no decoder error. The user reported that it booted past the black screen but then stalled loading. All three original movies were restored and their full asset-range hashes verified. The current installed configuration is again the original movies plus the camera mod.

`direct-archive/state.json` records original/patched hashes and exact offsets. `direct-archive/*.original.movie` contains verified full backups of all three original movies. `work/direct_intro_archive.py restore` restores the original prefixes after checking the installed bytes, backup hashes, unchanged index, and that the game/Overstrike are closed. Run it with the bundled Python runtime. The script refuses changed game or index versions rather than writing to unverified offsets.

Steam file verification will undo this direct archive edit. It is separate from an Overstrike stage mod. Rebuilding the Overstrike profile will not restore movie bytes; use the restore script or Steam verification to undo it.

## Previous tests and verified working baseline

The game reached the menu with the original intro movies and the camera mod enabled. Both the original NoIntro package and a locally prepared short clip caused a black screen in our reinstallation tests. The user also reports reaching the menu with both mods enabled earlier. This means an inherent incompatibility is not established; the cause remains unresolved. Decoder validation alone did not prove compatibility with the game’s startup sequence.

Before the direct archive diagnostic, the original intro movies were restored. Both Overstrike copies have `NoIntro.stage` disabled and `PhotoMode-10x-Tether1000.stage` enabled. The failed experimental replacement was removed from their profiles and libraries. The native camera DLL is unchanged.

The restored asset index differs from the Steam original only for the Photo Mode config asset `AED6101948AAFA54`. All three boot movies and all other asset records match the original. This is the same configuration the user confirmed reaches the menu.

`toc.BAK` now matches Steam depot 1895881, manifest 2186341403927512776, build 23987138: SHA-1 `64946f571579d9ea0a17e675682e2994dc0f20fc`. `toc.steam-original` retains that verified clean index. The earlier backup had already contained modded references; replacing it alone did not fix the legacy intro mod.

`isolation-verification.json` records the stable baseline configuration before the direct archive test. `compatible-intro-install-verification.json` records the failed experiment. `backup-before/` and the profile backups retain recovery files. Do not use modified recovery indices as clean Overstrike baselines.

After a future game update, verify game files before replacing Overstrike’s baseline. Never delete `toc.BAK` and reinstall while `toc` is still modded, because Overstrike would make that modified index the new backup. NoIntro is currently disabled while the startup cause is investigated. `../camera-controls/Reinstall-Camera.ps1` now guards the camera-only reinstall before and after installation; direct GUI use is not guarded by our scripts.

Relevant author reports: https://www.nexusmods.com/ratchetandclankriftapart/mods/5?tab=posts.

No LOD override has been installed yet. Its requested scope remains Photo Mode only.

