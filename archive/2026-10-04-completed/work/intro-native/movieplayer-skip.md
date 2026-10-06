# Native MoviePlayer stop/skip path

Read-only static trace of the installed game EXE. No game files or process memory were changed.

## Evidence

- `0x8a7c20` loads the singleton MoviePlayer at `0x61287a0` and jumps to update `0x8a78c0`. The update stores its state at `this+0x30`, current native movie slot ID at `+0x34` (16-bit), a small countdown at `+0x38`, and current path pointer at `+0x40`.
- The native video manager is global `0x52f4470`. Per-slot records are selected through manager `+0x58` with `0x160` stride. In each record, `+0x130` is the status/state, `+0x134` the slot ID, `+0x13c` a reset field, and `+0x18` the backend object. `0x112dd30` reads `+0x130`; `0x112e6a0` specifically checks whether it equals 4.
- The game's own input handler at `0x8abf10` obtains the active slot ID, checks configured input keys, and, on one branch while media status is 4, calls `0x11304c0`. That function only writes `2` to the selected slot's `+0x130`. This is the strongest candidate for the native stop/skip request: it is reached from game input handling and leaves the normal MoviePlayer update and cleanup machinery active. A second input branch calls `0x112ef70`, which writes status 3, clears `+0x13c`, and dispatches the backend object's virtual operation; `0x112ef40` toggles status between 3 and 4. These look like playback control/pause states, not the direct stop request.
- Normal cleanup is separate: MoviePlayer update calls `0x11305d0` when its own state machine reaches its exit path. That routine frees decoder buffers/handles and changes native slot state to 7. The inspected stop-request helper `0x11304c0` does not call cleanup, queue-ready, or ModeBoot completion itself.

## Calling convention and status-2 path

Both helpers use the Windows x64 register convention. `0x11304c0` receives the manager in `RCX` and the 16-bit slot ID in `DX`; it returns `void` and only sets the selected record's status (`+0x130`) to 2. `0x112dd30` receives the same arguments and returns that status as an `int` in `EAX` (zero for `0xffff` or an absent slot). The full bounded instruction extracts, including caller, are in `movieplayer-skip-disassembly.txt`.

When update state 6 polls status 2, it transitions to its own state 7. State 7 then sees status 2 is not 6 or 7, calls normal cleanup `0x11305d0`, invalidates its slot ID to `0xffff`, releases the current path object, and advances to state 8. State 8 either drains an already queued next path or advances to idle state 9/0. Thus status 2 follows the MoviePlayer's ordinary per-slot cleanup and queue progression; it does not directly set the separate ModeBoot/movie-resource-manager readiness byte. The game input handler calls the same helper, which is strong evidence for this being the intended stop/skip request path, but a runtime test is still needed to verify the boot queue advances correctly for this regional clip.

## Scope and implications

For a Photo Mode extension, the plausible scoped trigger is to call `0x11304c0(manager=0x52f4470, slotId=[0x61287a0+0x34])` once when the singleton MoviePlayer has a valid current slot ID and its current path is the regional `BootSequence_*` clip. The ID must be checked against `0xffff`; current path is at `+0x40`. This is a candidate for an experiment, not a verified patch recipe: the input handler also consults per-clip/input metadata, so directly calling the helper may omit policy checks even though it uses the same native status transition.

This request does not itself complete the movie resource queue or alter `toc.BAK`. The normal player update/cleanup remains responsible for release; ModeBoot's separate queue readiness is still a dependency. Therefore a native skip may avoid waiting for the full intro, but this static trace does not show that it can repair an archive/TOC backup problem or a hang caused by stale/broken movie resources. Likewise it provides no evidence that the camera feature itself damages `toc.BAK`; that depends on the mod installer/archive-writing workflow, outside this runtime trace.
