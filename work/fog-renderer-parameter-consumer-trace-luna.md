# Fog renderer preparation trace: compact block interpolation

Read-only native trace of the supported local executable. No executable, game data, process memory, source, or installation was modified.

## Result

`11D3500` prepares a 0x760-byte render-state block in `R14`. The active atmosphere's 0x8C bytes at source `+0x3EC..+0x474` are copied to `R14+0x110..+0x198` (`11D396B..11D39E1`). Fog texture refs are resolved into separate records `R14+0x348` and `R14+0x380` through `11D60F0` (`11D3B46..11D3B92`). The null-source branch initializes `R14+0x110` with `FB6770` and initializes other nested blocks with helper defaults (`11D3B9C..11D3C09`).

I found a real runtime preparation operation over the compact fog block inside `11D3500`:

- `11D43F5..11D43FE`: if global `65A3080` is non-null, call it with `RCX=R14` and `RDX=R13`.
- `11D4400..11D4426`: read global float `53393B0`, compare it to `XMM6`, clamp it between `XMM7` and `XMM12`, and form `sqrt(max(XMM12 - value, 0))` as a blend factor in `XMM6`.
- `11D442D..11D4438`: call `11DCF00` with `RCX=&53390E0` and `RDX=R14+0x70`; multiply its scalar result by global float `53393B4` into `XMM4`.
- `11D4448..11D448C`: interpolate floats at `R14+0x110`, `+0x114`, and `+0x118` toward `XMM4` using the factor in `XMM6`; store the third via a stack temporary. `11D448F..11D44A7` also interpolates `R14+0x11C` using `XMM12` and the same factor.

This proves those renderer-block values are modified during render-state preparation and that the block's first four floats participate in a continuous interpolation path. It does **not** establish camera-distance semantics: the shown calculation uses globals, `R14+0x70` context, and `R13`; I did not find a camera-position subtraction here. It also does not show the later GPU constant upload or the semantic names for these four destination floats, so they should not be called a particular fog distance, height, or color channel without another verified mapping.

## Renderer wrapper boundary

The `12BB250..12BB267` PDATA range is only a short fragment; its branch target `12BB632` is the return at the other end of the same wrapper flow. Disassembling that bounded fragment through `12BB632` shows `12BB250` receives the render block in `R8` (`mov rbp,r8` at `12BB274`), but directly reads only `R8+0x238` (float compare at `12BB285`), `R8+0x74C` (`12BB309`), and `R8+0x164` (`12BB53C`). It dispatches other rendering work and tails to `11E0D60` only when global `5339388` is nonzero (`12BB5D6..12BB5F8`). In the inspected `11E0D60` PDATA fragment, direct reads from its render-block argument are `+0x74`, `+0x78`, and `+0x7C`; this fragment does not reach the GPU upload.

The nearby `11D4A90` helper accesses the records starting at `R14+0x310` to maintain resource/lifetime bookkeeping. I found no evidence in this pass that it uploads fog-map contents or computes a fog mip choice.

## What this resolves

- The active source atmosphere does not need to change for renderer fog values to be adjusted: there is a native per-call/per-view block preparation path that performs interpolation after the atmosphere copy.
- The specific visible calculations above are interpolation, not proven distance culling.
- `work/live-atmosphere-readonly/corson-near-far-comparison.json` (parent-provided capture) reports identical 1696-byte atmosphere blocks, identical pointer and four registry slots, empty fog-texture records, and global `5339340=0` near/far. That observation is consistent with investigating per-view preparation/render use, but does not itself identify the cause of the white background bands.
- No reversible fog override is justified by this trace. Keep the source atmosphere and sliders intact; do not force these fields or texture records based on appearance alone.

## Evidence to continue

The next useful trace is the code behind the indirect vtable call at `11D43FE` and the graphics/render callback that consumes returned `R14` after `11D3500`; follow PDATA unwind-chain info for both because the nearby code contains split PDATA fragments. At those consumers, prove which fields are uploaded and whether the compact block's `+0x110..+0x11C` values or the resolved handles at `+0x348/+0x380` affect fog depth/mip or volumetric cutoff. The current bounded trace cannot establish those semantics.
