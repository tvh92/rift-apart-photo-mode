# Fog-map runtime reference use trace

Bounded read-only executable scan (same build as `AGENTS.md`), focused on the two named typed-reference records decoded at atmosphere `+0x478` and `+0x490`. The scan checked both record bytes and the resolver-populated pointer fields (`+0x480` and `+0x498`), as well as adjacent 32-bit fields. No executable, game asset, native source, or installation files were changed.

## Findings

The built parser `0xFAE710` calls `0xFB3D40` for the records at `+0x478` and `+0x490`. That helper resolves the display label **“Fog map texture”** and writes the resolved handle to each record’s `+8` member. Thus the runtime handle slots are `atmosphere+0x480` and `atmosphere+0x498`.

I scanned the existing branch-reference index for direct callers of active atmosphere lookup `0xFB1130` and fallback getter `0xFAE1A0`, plus the six known Photo getters that return active-atmosphere sub-blocks. Across those 44 unique caller functions, none directly reads or copies offsets `+0x478/+0x480/+0x488` or `+0x490/+0x498`; the only exact nearby-offset hit was an unrelated `lea r14,[r13+0x4A0]` at `0x12BC9E3`. Its local code reads other state and contains no access to the two fog-handle offsets.

A whole `.text` displacement scan does find many common immediate displacements of `0x478`/`0x480`/`0x490`/`0x498`, but without a dataflow link to the atmosphere object these are unrelated object fields. No direct shader-constant upload or fog-map-distance/mip calculation was found in the registry/accessor caller set. The visible native path is therefore still parser-side resource resolution only; a generic/indirect renderer copy or runtime asset-to-shader path remains unproven.

## Reproducible evidence

- Parser calls to fog-map typed-reference resolver: `0xFAECA9–0xFAED30`.
- Resolver helper and label: `0xFB3D40`, string RVA `0x32BF470` = “Fog map texture”.
- Output handle fields: `+0x480` and `+0x498` (`+8` within the two typed-reference records).
- Direct non-Photo scalar reader `0x1873030` reads other values (`+0x4AC..+0x4B8`); it does not read either fog-map record or handle.
- Registry/fallback caller scan: branch refs to `0xFB1130` / `0xFAE1A0`, intersected with displacements `{0x478,0x480,0x488,0x490,0x498,0x4A0}`; only hit was `0x12BC9E3` (`lea r14,[r13+4A0h]`).
