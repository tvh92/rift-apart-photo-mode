# Processed fog changes with view position

Bounded, read-only trace of the supported local executable and the saved near/far captures. No game process, executable, asset, source, or installation was written.

## Capture result

`work/processed-fog-near-far-comparison.json` records the same selected atmosphere source hash (`4aef590c…faca3`) at the Corson far and near Photo positions, while the prepared renderer fog block at `+0x110..+0x19C` differs. The far sample position is `(-122.581, 137.044, -234.327)` and the near sample is `(-75.671, 44.162, -40.871)`.

Values that change include:

| Prepared block field | Far view | Near view |
|---|---:|---:|
| `+0x110/+0x114/+0x118` | `(0.9734, 0.5711, 0.9734)` | `(0.2423, 0.1559, 0.2423)` |
| `+0x128..+0x138` (five height knots) | `[-200, -100, 0, 150, 600]` | `[-50, -10, 15, 50, 100]` |
| `+0x140..+0x14C` (four weights) | `[0.1, 0.005, 0.0035, 0.001]` | `[0.807, 0.309, 0.116, 0]` |
| `+0x174` | `64` | `48` |

The native preparation helper `0xFB5EF0` proves a camera-height dependency in this block: it reads camera Y from `[R9+4]` and subtracts it from the five height knots loaded from compact fog `+0x18..+0x28` (`0xFB61EE..0xFB6248`). It then evaluates the associated per-knot values and writes derived coefficients into its job/output record (`+0x6D4..+0x720`, stores at `0xFB649D..0xFB6680`). Thus the prepared height-fog curve is explicitly view-height-relative. The captures show a correlated change in the inputs to that curve as well; they do not prove which interpolation step selected those values.

The endpoint experiment changing `+0x174` from `64` to `128` and `512` did not visibly change the far view; both were restored to `64`. This makes that one endpoint a weak candidate for the observed white bands. It does not rule out the other changed height/color/weight fields.

## Native dataflow and limits

In render preparation `0x11D3500`, the base atmosphere bytes `+0x3EC..+0x474` are copied into prepared block `+0x110..+0x198` (`0x11D396B..0x11D39E1`). The same preparation routine then executes a regional-record loop. At `0x11D3E21..0x11D3E40`, it passes the current record and a position vector to `0x13A59B0`, passes the returned scalar and the record to `0x13A48C0`, scales the result, and branches on the resulting weight. `0x13A59B0` transforms the input position through a record transform (`0x162C150`), normalizes the transformed coordinates by record dimensions at `+0x50/+0x54/+0x58`, and dispatches shape/falloff math using the byte at `+0x86`. `0x13A48C0` further scales/clamps the scalar using record bytes `+0x33/+0x35`. These routines establish position-dependent regional weighting; their owning record type and user-facing names are not identified here.

For qualifying records, `0x11D3E9D..0x11D3EF9` applies weighted field operations to other prepared sub-blocks (`+0x3F8`, `+0x3C0`, `+0x430`, and a stack block). This is evidence for regional blending in the overall render preparation, but those particular destinations are not the compact fog block and I cannot attribute the near/far fog changes directly to these stores. The saved captures prove that processed fog changes while the selected source atmosphere stays the same; the precise writer for every changed fog member remains unresolved.

The shader reflection names `GlobalWorldCBuffer` fields `m_FogColor`, `m_FogConsts`, `m_FogDepthColorRange`, and `m_FogDepthColorScale` (`work/shader-fog-reflection-main.json`). I have not proven a byte-for-byte mapping from the `0xFB5EF0` job fields at `+0x6D4..+0x720` to those shader members. They should not be assigned those names solely by numerical proximity.

The indirect callback at `0x11D43FE` is backed by global slot `0x65A3080`. Existing registration/unregistration paths at `0x565BA4/0x565E67` and another registration at `0x9148C9` were traced in `work/fog-blend-config-callback-trace-luna.md`; the observed installed callbacks gate unrelated render-state fields and do not write compact fog `+0x110..+0x14C`. Therefore that slot is not evidence of an existing Photo-only fog override. Replacing its owner would need separate lifecycle/ownership proof before it could be used for pinning.

## Assessment

The strongest supported lead is the position-dependent prepared fog block, especially its changed color, height knots, and weights; the camera-Y subtraction then evaluates a different height-relative curve. This is consistent with a view-dependent fog change but does not prove the white background bands are caused by it. A one-frame/one-call comparison that holds the near prepared fog block while the camera remains at the far position is a reasonable reversible diagnostic. A persistent Photo-only override should wait for a proven call site/ownership path and an identified camera-context filter.
