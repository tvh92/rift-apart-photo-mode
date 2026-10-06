# Photo Mode vignette / grain field trace (bounded)

Read-only trace of the local Rift Apart executable build 23987138. No game, source, or installation files were changed. Existing protected `iced_x86` support was accessed read-only after the repository handoff allowed read-only escalation.

## Vtable method correction

The shared Photo Mode vtable methods in question are getters, not setters. Each performs the same sequence: resolve the global settings object rooted at RVA `0x52DDA20` through `0xFB1130`, fall back to `0xFAE1A0` if null, then return a pointer into the settings object:

| Method RVA | Returned address |
|---|---|
| `0x1A57D40` | global settings `+0x300` |
| `0x1A57D70` | global settings `+0x0F8` |
| `0x1A57DA0` | global settings `+0x4C0` |
| `0x1A57DD0` | global settings `+0x3EC` |
| `0x1A57E80` | global settings `+0x0A8` |
| `0x1A57EB0` | global settings `+0x524` |

These methods contain no option ID comparisons and write no data. The exact effect fields therefore cannot be assigned from these getters alone.

## Lifecycle and snapshot evidence

- Entry routine `0x1A56D70` snapshots outputs from shared vtable slots `+0xF8` through `+0x120` into Photo Mode object storage around `+0x770..+0x7E8`. The snapshot is preserved for later restoration; it is not itself a neutralizer.
- The getter at `0x1A57DD0` supplies the `global+0x3EC` structure. Entry reads its floats at `+0x2C,+0x30,+0x34,+0x38,+0x3C,+0x54` into Photo Mode snapshot fields `+0x7A0..+0x7B4` (and mirrored fields beginning `+0x770`). This is a concrete captured block, but there is no proven Vignette/FilmGrain label for any member.
- The getter at `0x1A57DA0` supplies `global+0x4C0`; entry copies its first four dwords to snapshot `+0x7C0..+0x7CC` and mirrors them at `+0x790..+0x79C`. Again, no effect label has been established.
- Exit at `0x1A57560` restores the parent-identified camera values from Photo Mode snapshot `+0x790..+0x79C` and renderer/global fields, confirming that entry snapshots are used for restoration. This does not establish a vignette or grain reset.
- `0x1A587C0` is an explicit one-time per-instance pointer-binding initializer: it returns early when `[this+0x7F8] != 0`, resolves hashed UI/settings bindings into pointers from `+0x6E8` through `+0x768`, and sets `[this+0x7F8]=1` at `0x1A58D12`. Its matched enum IDs include key-light elevation, azimuth, intensity, and light-grid intensity; none are vignette or film-grain IDs. It is not a demonstrated effect initializer.

## Option callback and enum mapping

RVA `0x1A5C170` is a one-byte getter (`return [this+0x7F9]`), not the generic option setter. Neighboring `0x1A5C1A0` is a generic event/object callback: it receives an opaque record, resolves an object through helpers, packs a type/index from object fields into `[this+0xAC]`, and forwards four 16-byte payload blocks at `[this+0x6C]`, `+0x7C`, `+0x8C`, and `+0x9C` through virtual callbacks. Its body contains no comparisons against the Photo option IDs.

The known hashes from `PhotoOptionIds.cs` are `VignetteIntensity=0xF9E4AD15`, `VignetteCenterClear=0x0C3445E4`, `FilmGrainSize=0x533F00B6`, and `FilmGrainStrength=0xE6A44C5A`. None appears in the one-time binder's decoded IDs or in the inspected shared getters. This callback did not yield a mapping from those IDs to a native renderer offset or a setter routine.

## Finding and safe next step

This trace establishes that the Photo Mode entry path captures existing state and exit restores it, while the inspected one-time binder handles other option families. It does **not** establish a concrete vignette/grain field or an effect-specific setter, so a neutral write at `global+0x3EC` or `global+0x4C0` would be speculative and should not be implemented. The `+0x3EC` and `+0x4C0` structures are concrete snapshot candidates for further field tracing, not verified effect offsets. Continue from the UI option consumer/renderer setter until an option hash reaches a specific float or packed field; then place any neutral assignment once after the guarded entry snapshot and leave slider callbacks untouched. Do not zero FOV or DOF as part of this trace.

## Local evidence

- `work/PhotoOptionIds.cs` (effect hashes)
- `work/lod-photo-disassembly.txt` / `work/lod-photo-vtables.json` (entry, snapshot, and shared vtable)
- `work/effects-main-continuation.txt` (parent's entry/exit field trace)
- Reproduced bounded decode with `work/disassemble_camera.py` plus an in-memory decode of `0x1A5C1A0..0x1A5C4BB`
