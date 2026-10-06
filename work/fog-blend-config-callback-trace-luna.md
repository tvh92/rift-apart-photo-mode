# Fog blend globals and callback registration trace

Read-only follow-up on `11D3500`, `11DCF00`, and globals `53393B0/53393B4`; no game, installation, process memory, or native source was modified.

## `11DCF00` behavior

Exact disassembly at `11DCF00..11DCF62`:

- If `RDX` is null or `[RDX] == 0`, it chooses a fixed-constant fallback (`11DCF04..11DCF3E`).
- Otherwise it takes a scalar from `RCX+0x288`, falling back to `[RDX+4]` if that config scalar is zero; it subtracts `RCX+0x290 + [RDX+0xC]` (`11DCF0E..11DCF30`).
- It applies a fixed scaling, calls a math helper, clamps the result with `maxss`, and returns (`11DCF3E..11DCF62`).

In the render-preparation call, `RCX=&53390E0` and `RDX=R14+0x70`. The block at `R14+0x70` is copied from the selected atmosphere source in `11D38DF..11D3906`. The helper therefore remaps data from the active atmosphere block using two values from the global config object. No camera position, camera-to-scene distance, or geometry depth is an input to this helper. A second caller in `12BC919..12BC989` uses the same helper for an output vector and the same config globals.

## Blend globals are persisted PhotoMode config state

The global-reference index shows these are actively written by configuration/UI code, rather than derived from camera location:

- `635F23..635F4B` reads object fields `[RBX+0x11720]` and `[RBX+0x11724]` and stores them to `53393B0` and `53393B4`; that function calls the settings service with the embedded key string `Photomode` (`2E696C0`). It then derives `53393B8` from the first value.
- `6361C9..6361E1` initializes those object members by copying the current globals back into `[RBX+0x11720]` and `[RBX+0x11724]`.
- The shared data-driven setter dispatch at `6397E9` includes a case at `639D6A..639D7A` that zeros `53393B4` and writes the selected floating value into `53393B0`; `63A0F8..63A118` is another setter that updates `53393B0` and recomputes `53393B8`.

This establishes that the blend pair are PhotoMode settings/configuration controls used to remap atmosphere values. The native traces do not expose their human-readable field labels, so I do not assign names such as “fog distance,” “fog intensity,” or “camera range.” Their effect can be atmosphere-dependent because `11DCF00` also reads active-atmosphere values, but they are not themselves camera-distance measurements.

## Indirect callback at `65A3080`

The setter at `11D4A80` is simply `mov [65A3080],RCX; ret`. One lifecycle path registers `&566440` (`565BA4`) and unregisters it with null (`565E67`); a second subsystem can register `&9161A0` (`9148C9`). `11D3500` conditionally invokes whichever callback is installed with `RCX=R14` (render block) and `RDX=R13` (render context).

The `566440` target is a conditional override callback, not the fog remap calculation: it returns unless `RDX == [6739B08]`; for that one context, flags gate clearing `RCX+0x108`, `RCX+0x13C`, and `RCX+0x164`, and a separate flag can tail-call `8E4E00(&6138200, RCX)`. It does not write the interpolated compact-fog floats at `RCX+0x110..0x11C`. The other registered target `9161A0` is a general set of scalar multiplications over its input object, with no direct `11DCF00` or `53393B0/53393B4` references in its bounded body.

## Conclusion

The interpolation path is a configured atmosphere-value remap followed by blending into the render block. The settings are sourced from the `Photomode` configuration key and are not computed from camera distance. The callback at `65A3080` is a context/flag-gated override path for other render-state fields; it does not explain the fog color interpolation. Concrete field labels and the eventual GPU upload remain unresolved, so changing these values would risk altering PhotoMode settings globally without proving a neutral default.
