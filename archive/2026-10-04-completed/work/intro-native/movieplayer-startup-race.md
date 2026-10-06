# Short-clip startup timing: native MoviePlayer trace

Read-only static trace of Rift Apart's installed EXE. User runtime results reported separately: four original frames (~0.13 s) blackscreen; 60 original frames (~2 s), original audio/codec and same archive index, reaches menu. TOC was byte-identical across the short-clip substitution, so the contrast points to clip content/duration rather than TOC serialization.

## What the native update proves

- The `ModeBoot::Update` path calls MoviePlayer update `0x8a78c0` before advancing its own state machine on each tick (`0x8a74ec`–`0x8a74f8`; see `modeboot-update.txt`). Its movie-resource queue readiness check is a separate call to `0x10cb0d0` later in the ModeBoot state path.
- When a path is selected, MoviePlayer `0x8a79b9` makes a native media request via `0x112e730`, writes the returned 16-bit native slot ID to `this+0x34`, enters own state 5, and initializes `this+0x38` to 3 (`0x8a79f1`–`0x8a7a06`). `this+0x40` is passed as a source/path-related argument; `this+0x28` is passed separately. Full bounded disassembly is in `movieplayer-startup-race-disassembly.txt`.
- State 5 calls `0x112ef70` each update, decrements the 3-tick counter, and only after it expires polls `0x112dc70`. This getter returns the dword at `+0x0c` of the backend object stored in the selected media slot's `+0x18`; invalid slot/object returns 0. If the value is `<=2`, MoviePlayer stays in state 5 and polls again on later ticks. Only a value `>2` moves it to state 6 (`0x8a7a89`–`0x8a7aed`). This is a minimum of three MoviePlayer update calls before polling the backend initialization/status gate, not a hard-coded minimum movie duration or frame count.
- State 6 then polls the *different* native slot state at media record `+0x130` through `0x112dd30`. Values 2 or 7 move the player to state 7; state 7 performs cleanup `0x11305d0` for status 2 and advances to its pending/idle path. The full caller/control traces are preserved in `movieplayer-skip-disassembly.txt`.

## Interpretation and remaining uncertainty

The 3-update delay plus the `backend status > 2` gate is a plausible initialization-versus-end-of-stream race for a 0.13-second clip. The static code does not reveal the backend status enum names, whether status `>2` means fully initialized or already terminal, or how BK2 frame count maps to its transitions. The 60-frame success and four-frame blackscreen with identical TOC strongly support a length-sensitive playback path, but do not prove that this specific gate is the cause. No minimum duration threshold is visible in MoviePlayer; ModeBoot separately uses the streaming-queue readiness and its own elapsed-time logic.

No native bypass or game changes were made.
