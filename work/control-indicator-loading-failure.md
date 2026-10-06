# Loading regression and rollback — 5 October 2026

Follow-up: the user confirmed the7508 rollback works. A revised lazy indicator7d4234168e04020b65bd2af2a88314bffe9bef2baadeb2994c2901b539008665 is now installed, awaiting startup/Photo tests. Read `work/lazy-indicator-current.md` for current status; below describes the earlier failure and rollback.

The user reported that the game was stuck loading again on the Ctrl/indicator build `06ce078afaca25aeb95cca6da595ea8f8b54f8a9ccac3aef833c64fadb6a6de8`. No game process was running when checked, so the failed log was preserved and rollback could proceed safely.

`work/control-indicator-loading-failure-2026-10-05.log` records successful proxy/collision/geometry/camera hook initialization, then Photo lifecycle states14,10,11 with native geometry preference. It never reaches active Photo state4 or shows a status card. This is not proof that a specific hook or indicator caused the stall. The indicator worker starts during initialization and creates a hidden native window, even though it only draws a card later; that new startup activity remains a hypothesis to test after confirming the baseline.

The installed DLL is now the previous geometry build `7508bd33654d057202fbd91b8c81d8622dca1c1e781c21b52ce82023fa14b272`, restored using the guarded `Restore-PreviousLODDLL.ps1`. It retains speed/no-clip and the Ctrl+Alt+L geometry toggle, with no status window. The user had successfully run this build for scene comparisons. The rollback passed the complete file audit: same four asset overrides, matching manager libraries/profiles, pristine TOC backup, vanilla base config, original movie bytes and supported executable. No intro, asset, profile, save or settings change was made.

The Ctrl/indicator build remains preserved for diagnosis and must not be reinstalled unchanged. The current test is to launch the restored previous build and establish whether normal startup returns. Do not claim the loading problem fixed until the user confirms. Do not change files after requesting that launch test.
