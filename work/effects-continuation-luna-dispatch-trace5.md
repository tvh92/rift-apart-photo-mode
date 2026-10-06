# Photo Mode numeric dispatch and +0xAC field correction

Read-only trace of executable build 23987138. No source, game, or installation files were changed. This report supersedes the earlier provisional ID13 interpretation in `effects-continuation-luna-dispatch-trace4.md`.

## UI callbacks

- `0x635170` is a `ScreenUIElementPhotoModeOptions` lifecycle/update callback. It checks UI state, resolves the option/list object, forwards callbacks, and sets `[option+0x47C]=1`; it does not write renderer effect fields.
- `0x1A5AED0` is a state transition: unless `[this+0x50]==8`, it clears `[this+0x3FC]`, saves the prior state from `+0x50` to `+0x4C`, then sets `[this+0x50]=8`. It is not a Photo option setter.
- `0x170D280` stages UI array/list values by group and list index; it has no native renderer effect writes.
- `0x1A5C1A0` is generic option/event plumbing. It packs a runtime type/index value into `[r15+0xAC]` from fields of a resolved object and passes payloads to callbacks. That `r15+0xAC` belongs to a different class than the Photo Mode system object's scalar `+0xAC`; the identical offset must not be conflated.

## Lifecycle state and native dataflow

`[PhotomodeSystem+0x50]` is a lifecycle/state enum, not the `PhotoOptionIds` enum. The evidence is the constructor `0x1A58550`, which initializes it to `0xE` (closed/default), and state transition routines which assign lifecycle states. Therefore the compares against `0xA`, `0xB`, and `0xC` in `0x1A591A0` do not mean Vignette, CenterClear, or GrainSize.

Within that lifecycle state machine:

- `0x1A5A0B0` copies `[this+0x88]` to `[this+0xAC]` while copying other saved fields into their working counterparts (`+0x6C=>+0x90`, `+0x70=>+0x9C`, `+0x74=>+0xA0`, `+0x7C=>+0xA4`, `+0x80=>+0xA8`).
- `0x1A591A0` later reads the Photo Mode system's float `[this+0xAC]` and writes it to global RVA `0x5339370` at `0x1A597BB..0x1A597C3`, in a broader update path gated by lifecycle state and a virtual predicate. This proves a saved-state dataflow, not an effect-option assignment.
- Entry `0x1A56D70` snapshots existing global `0x5339370` into `[this+0x88]` at `0x1A56ECB..0x1A56EDA`; exit restores from `+0x88`. The matching snapshot/restore strongly ties `+0x88/+0xAC` to the lifecycle's saved/working copy of that global value, but the field's effect name is still unproven.
- Constructor `0x1A58550` zeroes a qword at `[this+0xA8]`, which includes `+0xAC`. In lifecycle functions, `+0xAC` is copied from `+0x88`, so constructor zeroing is not evidence of a FilmGrainStrength default.

The native option enum order is known (`PhotoOptionIds.cs`: IDs 10..13 are VignetteIntensity, VignetteCenterClear, FilmGrainSize, FilmGrainStrength). This investigation found no native setter dispatch that maps those IDs to `[PhotomodeSystem+0xAC]`, global `0x5339370`, renderer `+0x388/+0x38C`, or another named effect field. Do not use the numeric overlap in the lifecycle state machine to infer option semantics.

## Neutralization and remaining limit

The entry snapshot at `0x1A56D70` still provides a structurally safe place for a one-time neutral write *after* preserving the original value, with exit restoration intact. However, without proving the named effect represented by `0x5339370` and the actual native option setter for vignette/grain, writing zero there or to the lifecycle object's `+0xAC` would be speculative. No effect-specific neutralization recommendation is established by this trace. Do not repeatedly overwrite live UI slider values, and do not zero FOV or DOF.

## Reproduction

- `work/effects-continuation-luna-rtti.py` enumerates the relevant Photo Mode RTTI classes and vtables.
- `work/disassemble_camera.py` plus bounded iced_x86 decodes produced the methods above.
- A bounded instruction scan of Photo/UI code ranges enumerated `+0xAC` accesses and exposed distinct object roles: Photo system lifecycle copies (`0x1A5A0B0`, `0x1A591A0`), generic callback's packed field (`0x1A5C388`), and a different pointer-bearing event object (`0x1A5C70A..0x1A5C768`).
