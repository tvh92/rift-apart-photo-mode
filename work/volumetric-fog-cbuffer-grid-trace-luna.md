# Volumetric fog shader constant and Z-grid trace

Read-only evidence from native render callbacks and embedded DXBC RDEF reflection. No game process, installation, assets, or native source modified.

## Shader constant-buffer mapping

The four embedded `VolumetricFogScatteringCBuffer` RDEF records at executable offsets `0x3C774FC`, `0x3C863EC`, `0x3C8853C`, and `0x3C8EC8C` agree on the same 352-byte `g_VFog` layout. These are shader reflection names/offsets, not labels inferred from host struct arithmetic:

- `g_VFog.m_GridZParams` is CB `+0x110`.
- `g_VFog.m_HeightFade` is CB `+0x120`.
- `g_VFog.m_Opacity` is CB `+0x130`.
- `g_VFog.m_Color` is CB `+0x134`.
- `g_VFog.m_InvZExtent` is CB `+0x150`.
- `g_VFog.m_DispatchOffset` is CB `+0x158`.

## Host upload and grid-depth derivation

`FB53B0` is the registered native `VolumetricFog` callback. It obtains the active renderer block from global `6732C48` and skips the volumetric pass when renderer block `+0x164` is not positive (`FB53EF..FB53F6`). On the positive-opacity path it calls the upload/setup routines `FB6890` and `FB6C90`.

`FB6890` writes fields to the reflected cbuffer as follows:

- renderer block `+0x164` -> CB `+0x130` (`m_Opacity`), at `FB6B8D..FB6B9A`.
- renderer block `+0x158..+0x160` -> CB `+0x134..+0x13F` (`m_Color`), at `FB6B9A..FB6BB8`.
- renderer block `+0x170` and `+0x174` determine CB `+0x150` (`m_InvZExtent`): `FB6BEC..FB6C14` subtracts `+0x170` from `+0x174`, clamps the extent above a small positive epsilon, computes `1/extent`, and stores it at CB `+0x150`.

`FB6C90` also derives grid X/Y counts by multiplying viewport pixel extents by configured grid dimensions, dividing by renderer `+0x448/+0x44C`, and rounding upward (`FB6CCC..FB6D95`). It then submits those dimensions with the volumetric compute resources (`FB6D95..FB6E99`).

Together, the named callback and the shader reflection prove that `+0x164` is the positive-opacity enable guard for the volumetric pass, and that `+0x170/+0x174` define the Z extent reciprocal used by the volumetric fog grid. This path uses an authored/render-state Z range and viewport/grid dimensions; it contains no camera-to-scene distance calculation. These instructions do not, by themselves, prove the *source-authored names* for `+0x170/+0x174`; the source-to-render offset/name mapping must still be established from the native decoder/schema path.

## Scope and limits

The shader reflection does not include the original HLSL source, but it definitively labels CB slots and host uploads. The pass's grid Z normalization can therefore be distinguished from the compact color/opacity remap (`R14+0x110..+0x11C`) traced earlier. A zero or invalid opacity prevents the volumetric pass; altering the far extent would affect volumetric depth sampling/coverage, not extend geometry draw distance. Do not override either field until the runtime source offsets are proven and a reversible scope is defined.
