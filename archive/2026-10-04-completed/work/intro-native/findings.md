# Rift Apart native boot-video path (read-only)

## Evidence

- `RiftApart.exe` contains the region-specific paths `movies/Boot/BootSequence_China.movie`, `..._EU.movie`, `..._PC.movie`, and `...GRAC_Korea.movie` at file offsets `0x2fb0b48`–`0x2fb0bc0`.
- The PC path maps to RVA `0x2fb1998`; its sole RIP-relative code reference is at RVA `0x8a7397`. The containing bootstrap routine is RVA `0x8a7350`–`0x8a744f` (disassembly in `bootstrap_routine.txt`). It selects a region movie path, stores it in the boot-video queue/state, optionally adds the Korean GRAC movie after an additional condition, then transfers to `0x10cb0f0`.
- A string scan found no `skipintro`, `skip_intro`, `nointro`, `noboot`, `nomovie`, or `nosplash` command/config tokens in the executable. This only establishes that those literal names are absent; it cannot rule out an undocumented numeric switch.
- `SkipIntro` is grouped with `SkipOutro`, `UseDestinationFacing`, `IgnoreHero`, and `StopForHero`, near the unrelated `Queue a Face command` / `BotCommand - Face` metadata. `SkipIntroPath` is explicitly grouped with curve-following fields; its nearby description says it controls whether to make/follow an intro path to a curve start. These are animation/action metadata, not boot-video flags.
- The `BootSequence` string at RVA `0x2e696f8` is adjacent to `LoadingScreen` and `DebugMenu`. One reference is generic config/UI field setup; another calls a generic bool getter for `BootSequence` and `LoadingScreen` before a UI-state operation. That is not the movie-path selection code and does not provide a skip-video switch.

## Conclusion

The native evidence shows a hard-coded regional boot-video selection/queue path and no literal skip-intro, no-movie, no-boot, or no-splash flag. `SkipIntro`/`SkipIntroPath` refer to animation behavior. No boot-video bypass was tested or applied.
