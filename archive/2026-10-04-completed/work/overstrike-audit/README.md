# Overstrike / NoIntro investigation

Date: 2026-10-04. Current Steam build: 23987138, depot 1895881 manifest 2186341403927512776.

## Confirmed local findings

- After the user's latest reset/Steam verification, `toc` was pristine (SHA-1 `64946f571579d9ea0a17e675682e2994dc0f20fc`) and `toc.BAK` was absent. The locally built camera `hid.dll` remained; Steam did not remove it. The asset camera stage was no longer active in the index.
- Both Overstrike copies are identical: SHA-256 `352be024109c81604d2e1109adb29bab5493f0290779fc296e0c75f61dfa5565`, product version `1.0.0+5829f3b045397ed19a1c3f282de504ba57197b7b`. That commit matches the official OS/v1.8.1 release. Both libraries contain byte-identical NoIntro and camera packages.
- Five installs using that actual executable targeted workspace copies of the pristine index: empty, camera only, NoIntro only, both in the usual order, and both in reverse order. Every install succeeded. Empty installation left TOC byte-identical to the Steam original. Each modded install changed only its expected asset records, appended only the expected archives, preserved all original archive entries and all other section payloads, and wrote byte-exact package payloads. Every created backup remained pristine. Results: `offline-results.json`.
- Thus the original NoIntro package's headerless metadata is handled correctly in these tests. The lowercase pre-hashed-ID source bug described in `findings.md` is not demonstrated for this package: the installed BK2 bytes are complete and unchanged. The metadata/payload test does not establish game-runtime streaming or playback compatibility.
- The user reports earlier successful menu entry with both mods. Later reinstallation tests failed. The legacy clip written directly into original archive offsets booted past black but stalled loading for 30-90 seconds; usual loading is under 10 seconds. Original movie bytes were restored and verified before the latest Steam reset.

## Current discriminating launch test

`Intro-Original-Routing-Test.stage` contains all three **unchanged original** regional boot movies extracted from the verified local game. Its only intended effect is routing those bytes through Overstrike's mod archive. The original movie content, codec metadata, audio tracks, and lengths remain unchanged.

The diagnostic was installed through a separate profile at `outputs/startup-repair/routing-launch-original`. Ordinary manager profiles were not modified. Installation validated exact TOC SHA-1 `78ee66e82f32eedf237490a7239c8d7f7760ebff`, fresh pristine `toc.BAK`, and byte-exact archive against the isolated workspace run. Native camera DLL is unchanged. The original-video routing test reached the menu.

If this reaches the menu, the next candidate is `NoIntro-Padded-CurrentBuild.stage`: four original frames, preserving original codec/audio metadata, two audio tracks, and original TOC asset lengths with zero padding beyond the BK2 file's declared end. Both packages were installed in isolated folders and produce **byte-identical TOCs**, so the next comparison changes only video payload bytes. The padded short clip decoded four frames with the installed Bink runtime. Neither padding nor this version is a confirmed fix until tested in-game.

If unchanged original videos also stall when routed through Overstrike, it demonstrates a movie-routing/runtime interaction for this configuration rather than corruption of the replacement clip. It still would not, alone, identify whether the fault is Overstrike's archive output or the game's streaming expectations.

## Current primary sources

- [Official README troubleshooting](https://github.com/Tkachov/Overstrike/blob/main/Overstrike/README.txt): stale backups after updates, interrupted installs, other file changes; TOC reset procedure.
- [Backup preparation/source](https://github.com/Tkachov/Overstrike/blob/main/Overstrike/MetaInstallers/MetaInstaller_I29.cs): create `toc.BAK` only if absent, restore it before installation, log a modified-index warning rather than reject it.
- [Stage installer source](https://github.com/Tkachov/Overstrike/blob/main/Overstrike/Installers/StageInstaller.cs): headerless metadata parsing and archive entry handling.
- [Latest releases](https://github.com/Tkachov/Overstrike/releases): 1.8.1, release changes concern MSM2 suits.
- [NoIntro author/community reports](https://www.nexusmods.com/ratchetandclankriftapart/mods/5?tab=posts): historical successful TOC resets; a 2026 report of failure after the latest game update.

Issue-list coverage and limitations are in `issues.md`. No specific public RCRA installer regression was established by that search.

## Final result

The four-frame padded clip black-screened. The two-second (60-frame) padded clip reached the menu. It was repackaged without changing asset payloads as NoIntro-Fixed-2Seconds.stage and installed alongside the camera mod in both ordinary profiles. Legacy NoIntro is disabled. The final file audit passed and the user confirmed the short intro reaches the menu and both normal/Shift Photo Mode speeds work. This supports a length-sensitive video startup issue in this configuration; the exact minimum or internal race is unproven. The clean backup remains correct.
