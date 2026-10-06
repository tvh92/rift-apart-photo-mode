# ModeBoot movie streaming path

## Trace

- `ModeBoot::Update` candidate RVA `0x8a74d0` is a state machine. In the movie-wait state it calls `0x10cb0d0` on the `0x52f2cb0` movie queue; this returns true only when the selected queue slot has state byte `3`. After playback timing reaches its limit, the routine calls `0x10cb0f0` for queue slots 2 and 3, then returns to the boot-mode completion path (`0x8a77a7` onward). Full disassembly: `modeboot-update.txt`.
- Queue processing is `0x10cb110`. Entries are 40 bytes apart; per-entry path/source pointers are read at `+0x20`, type/key at `+0x28`, stream bookkeeping at `+0x18/+0x30`, and status at `+0x3c`. It asynchronously advances entry states, obtains the data source via `0xfa42e0`, then requests the file stream through `0xfa7870`. Readiness/completion bookkeeping is handled by `0x10cb0d0/0x10cb0f0`.
- In `0xfa7870`, `rdx` is the selected path pointer. The function first checks an optional global callback pointer at `0x6203e58`, passing the path; if the callback reports handled, it returns null. Otherwise it performs a lookup using the stream context at `rcx+8`.
- The generic path lookup is `0x15acde0`, which uses `0x15ad530` to hash the path and probe the context’s hash table. On a hit, it returns `table_base + entry_index * entry_stride` (context fields `+0x8` and `+0x20`). This is evidence for hash-based lookup in the selected archive/container context. It is not a string-based prefix lookup for `d/mods` inside this function.

## Redirect conclusion

This trace does not prove that boot streaming ignores the mod overlay. The resolver accepts an optional dynamically supplied callback before falling through to the container hash table; the executable has only a read reference to callback global `0x6203e58` in the traced code, so this inspection does not identify who sets it or whether Overstrike uses it for boot movies. The selected boot path is passed into generic stream resolution; no explicit `d/mods` path construction appears in the traced functions. Establishing overlay precedence requires tracing the callback installation or inspecting the runtime container table for the boot path, which this read-only static pass did not do.

No game files or process state were changed.
