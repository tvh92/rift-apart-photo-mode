# Working two-second intro replacement

`NoIntro-Fixed-2Seconds.stage` is installed in both Overstrike libraries and enabled alongside `PhotoMode-10x-Tether1000.stage`. The original `NoIntro.stage` is disabled. The native camera DLL is unchanged.

The replacement contains 60 original frames (two seconds at 30 fps) from each regional boot video. Original codec settings, both audio tracks, and original TOC asset lengths are preserved; bytes after the shortened BK2 file are zero padding. The compressed package is about 2.4 MB; its installed movie archive is about 94.6 MB. The original `d/movie` archive is untouched.

The user confirmed that this two-second payload reaches the main menu. The permanent package has identical asset payloads to that successful test. A four-frame version (about 0.13 seconds) with the same TOC layout produced a black screen, while the full original movies loaded successfully through Overstrike. This establishes length-sensitive behavior for those tested clips, not the exact minimum duration or a proven internal race. Static analysis shows asynchronous video setup and a three-update delay before the player checks backend status.

Both the permanent package's installed payloads and the camera config have been audited against both libraries. Only the three boot-video records and the camera config record change; all other index sections and asset records are preserved. `toc.BAK` matches Steam's current clean baseline.

## Reinstall or disable

In Overstrike, leave legacy NoIntro unchecked, check **Skip intro (current build, 2 seconds)** and the camera mod, then install. Either manager copy has the same configuration. `../camera-controls/Reinstall-Camera.ps1` adds baseline and payload checks around the current supported profile. Close the game and manager before running it.

To restore the normal intro, uncheck the fixed intro and install the profile again. Original movies remain in their base archive. After a future game update, establish a fresh Steam-verified index before reusing a backup. The guarded installer rejects changed builds or contaminated backups. Direct Overstrike GUI use has not been patched to enforce those checks.

The exact game/backup versions and detailed tests are in `../../work/overstrike-audit/README.md`. This is a local compatibility package, not an update published by the Nexus mod's original author.
