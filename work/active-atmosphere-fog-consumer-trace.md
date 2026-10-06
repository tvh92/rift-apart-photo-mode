# Active-atmosphere scalar consumer trace

Read-only xref/disassembly trace for the local executable build documented in `AGENTS.md`; no executable, game asset, source, or installation writes. This follows direct callers of the active-atmosphere registry and fallback getter, then filters them for accesses near the named fog-map references (`+0x478/+0x490`) and associated scalar region.

## Confirmed non-Photo reader into render-state storage

The branch xref index identifies function `0x1873030` as a non-Photo caller of `0xFB1130` (call at `0x187351B`). It passes registry `0x52DDA20` and the index held in `[rbx+0x10C]`, then reads the returned atmosphere object:

```asm
01873514 lea rcx,[rel 52DDA20h]
0187351b call 0000000000FB1130h
01873525 movss xmm2,[rax+4B8h]
0187352d movss xmm3,[rax+4B0h]
01873538 maxss xmm1,xmm2
0187353f comiss xmm1,xmm0
01873544 movss xmm10,[rax+4ACh]
0187354d movss xmm9,[rax+4B4h]
01873556 movaps xmm11,xmm3
0187355a movaps xmm8,xmm2
```

If the larger of `atmosphere+0x4B0` and `+0x4B8` is positive, this function takes all four floats from `+0x4AC/+0x4B0/+0x4B4/+0x4B8`, scales some by an incoming factor at `[rbx+0xEC]`, and runs the resulting values through interpolation/smoothing math. It then calls `0x124DC80` at `0x18736EF`. That helper obtains a state object and calls `0x1237CD0`; the latter writes the passed scalar/vector state to object members `+0x1DA4`, `+0x1DA8`, `+0x1DAC`, `+0x1DB0`, `+0x1DB4`, and `+0x1DB8` (RVA `0x1237CD0–0x1237D16`). This is a concrete active-atmosphere-to-render-state data path, rather than Photo snapshot or registry management. However, `0x124DC80` is a generic state-queue helper: sibling callers use it with type value `5`, while this caller supplies type `3`. Therefore the sink is not, by itself, evidence of a fog shader upload.

The same built-atmosphere parser maps the four-float group exactly: source block `+0x440/+0x444/+0x448/+0x44C` is copied to output object `+0x4AC/+0x4B0/+0x4B4/+0x4B8` at `0xFAED47–0xFAED4E`. The preceding source float `+0x438` is copied to destination `+0x4A8` at `0xFAED30–0xFAED3F`.

This proves the scalar group's serialization and consumer. It does **not** establish a field name such as `FogSettings.ColorMapDepthRange` or `VolumetricFogSettings.FarDistance`: the consumer does not dereference the confirmed fog-map pointers at `+0x478/+0x490`, and this path does not emit a camera-distance or fog-mip computation that identifies the four floats' authored semantics. The values are passed through interpolation into a render-state structure, but the rendering system/state fields themselves remain unnamed in the examined code.

## Other observed accesses

- Photo-specific callers `0x1A56D9B`, `0x1A5AA10`, `0x1A57DA0`, and exit/reset routines use registry values in the `+0x388`, `+0x3D8`, `+0x4C0`, and `+0x524` areas already described in `photo-renderer-light-fog-paths.txt`; these are not the non-Photo scalar consumer above.
- Fallback caller `0xFC6C6C` calls `0xFAE1A0` at `0xFC6E26`, compares the fallback pointer against a selected atmosphere, and when they differ reads `[selected+0x540]` and `[selected+0x544]` into an output record at `[rbx+0x9C/+0xA0]`. That caller provides no field name, distance calculation, or direct fog-map access.
- The branch-reference callers inspected did not read the texture-reference pointers at `+0x478` or `+0x490` directly.

## Conclusion and limit

There is now a proven non-Photo consumer of the live current-atmosphere object, with an exact built-file source-to-runtime mapping for four adjacent floats and a downstream generic render-state write. It is a useful next breakpoint/controlled-runtime-capture location (`0x187351B` for the read, `0x1237CD0` for the sink), but static evidence alone does not identify these floats as the reported fog transition controls or prove that the final state is uploaded as fog shader constants. Do not patch these offsets based on this trace alone.

## Reproducible RVAs

- Registry getter: `0xFB1130`; registry global `0x52DDA20`.
- Non-Photo consumer: `0x1873030`; registry read at `0x1873514–0x187355A`.
- Source-to-destination copy: parser `0xFAE710`, scalar copy at `0xFAED30–0xFAED4E` (`source+0x438` to `dst+0x4A8`; `source+0x440..+0x44C` to `dst+0x4AC..+0x4B8`).
- Render-state wrapper/sink: `0x124DC80` -> `0x1237CD0`; writes begin `0x1237CE2`.
- Fallback caller: `0xFC6C6C`; fallback compare/read at `0xFC6E26–0xFC6E53`.
