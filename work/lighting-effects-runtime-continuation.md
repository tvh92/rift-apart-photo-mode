# Fog runtime consumer trace continuation

Bounded, read-only disassembly against local executable build 23987138 (EXE SHA256 in `AGENTS.md`). I read the current `AGENTS.md` first. No native source, game files, or installation state were changed. The reported pit-fog transition is still unresolved; this pass followed the native atmosphere synchronization/blending classes identified by RTTI and did not locate the final PC renderer consumer.

## Confirmed native path fragments

- `AtmosphereSyncComponent` RTTI vtable is RVA `0x32BEEF0`. Its ten entries include `0xFB0C00`, `0xFB0BE0`, `0xFB0BF0`, `0xFB0C30`, `0xFB0D00`, and `0xFB0D50`.
- `0xFB0C30` builds/serializes four entries from a static descriptor array at RVA `0x6240BB0`, using the generic metadata and DDL helpers at `0x1321330`, `0x1322B00`, `0x1322F40`, and `0x1322DC0`; it marks static flag `0x6240BD0`. It does not read a camera, `FogSettingsDef`, or `VolumetricFogSettingsDef` member.
- `0xFB0D00` unregisters 32 records against the global registry at `0x52DDA20`. It is teardown, not a live parameter setter.
- `AtmosphereBlender` vtable is RVA `0x4632AF0`. Method `0x1BA2F90` loops through a caller-supplied list and invokes generic DDL data helpers (`0x15B9270`, `0x15BBC50`, `0x15BAE20`); method `0x1BA3080` funnels a caller-supplied value into generic dispatcher `0x15BF860` / `0x15BE0D0`. No direct fog field displacement or camera argument appears in these bodies. This establishes generic atmosphere blending/data dispatch, not a renderer write.
- `AtmosphereBlenderPrius` vtable is RVA `0x46A88D8`. Its methods mostly return type/schema descriptors or construct/destruct a small event record (`0x1D2FC90`, `0x1D2FD20`); no fog consumer was present in those methods.

## Relation to the fog schema candidates

Previously confirmed reflection metadata gives `AtmosphereDef.FogSettings` at `+0x4B8`, `VolumetricFogSettings` at `+0x588`, `FogSettingsDef.ColorMapDepthRange/+0x58`, `ColorMapDepthScale/+0x5C`, and `VolumetricFogSettingsDef.NearDistance/+0x64`, `FarDistance/+0x68`. The metadata describes the color-map mip transition and replacement of height fog by volumetric fog up to the far distance. This runtime trace does not prove that any of these values are read by the current PC renderer with the Photo camera.

## Hook/override conclusion

No concrete reversible Photo-only argument override is justified by the examined methods. The surviving evidence supports only schema-level hypotheses: a high mip in the fog color texture could be pale, and the volumetric/height-fog distance handoff could change with view distance. There is no proven active asset/value, renderer setter, consumer argument, or callsite tied to the symptom. Do not patch the schema offsets or keep overwriting them from a Photo update loop on this evidence. Next useful evidence would be a renderer-side function that receives the active camera position and a concrete atmosphere/fog parameter block, or a controlled runtime capture that identifies the active fog block/value while reproducing the symptom.
