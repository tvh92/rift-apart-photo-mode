# Active atmosphere fog-block identity trace

Bounded read-only disassembly of the local executable build documented in `AGENTS.md`. No executable, game asset, native source, or installation files were changed. This pass followed the default atmosphere initializer and the built-atmosphere decoder around their fog and grain resource references. It identifies named texture-reference slots in the active atmosphere object, but does not prove a numeric distance/color field mapping or a renderer consumer.

## Proven object and decoder relationship

The existing `built-atmosphere-native-loader.md` trace establishes that `0xFAE710` decodes the `Atmosphere Built File` base section (`0x02F06D4E`) into the same atmosphere object exposed by the current-atmosphere registry. `0xFB1130` returns registry slot 0 from `[registry+0x1C8]`; Photo getters call this lookup. `0xFAF910` initializes the static fallback object returned by `0xFAE1A0`.

## Named resource slots

At `0xFAECA9–0xFAED30`, the decoder copies two serialized groups into destination blocks `atmosphere+0x478` and `atmosphere+0x490`, then calls `0xFB3D40` for each. `0xFB3D40` checks the typed-reference tag `0x95A3A227`, passes the descriptor string at RVA `0x32BF470` to resolver `0x1358410`, and stores the resolved pointer. The descriptor string is **“Fog map texture”**. This directly names two fog-map texture reference slots; it does not name nearby scalar values as fog distances or colors.

At `0xFAED55–0xFAED90`, the decoder copies a group to `atmosphere+0x4D0` and calls `0xFB3E80`. That helper uses descriptor string RVA `0x32BF4B8` = **“Film Grain Noise Texture”**. It identifies this texture reference only.

The default initializer `0xFAF910` initializes the same destination areas: references at `+0x478`, `+0x490`, and `+0x4D0`; intermediate members around `+0x4A8–+0x4C0`; and a later block around `+0x4E8–+0x510`. It sets `+0x4B4` to float `100.0`, `+0x4B8` to `0`, `+0x510` to `-1.0`, `+0x524` to `15.0`, `+0x52C` to `60.0`, `+0x534..+0x53C` to `1.0`, `+0x540` to `0.1`, and `+0x544` to `1000.0`. These are constructor defaults at those object offsets, not identified fog controls; assigning them names from numerical proximity would be speculation.

## Why DDL offsets do not name these members yet

The native DDL metadata trace reports `AtmosphereDef.FogSettings` at `+0x4B8`, `VolumetricFogSettings` at `+0x588`, and child members `FogSettingsDef.ColorMapDepthRange/+0x58`, `ColorMapDepthScale/+0x5C`, `VolumetricFogSettingsDef.NearDistance/+0x64`, and `FarDistance/+0x68`. The built decoder is a custom packed `0x02F06D4E` parser: it explicitly copies fields from different source offsets into its runtime object and invokes typed resource resolvers. No code examined here converts a `FogSettingsDef` DDL object at parent `+0x4B8` or a `VolumetricFogSettingsDef` at `+0x588` into this custom output layout. Therefore the DDL offsets cannot safely be added to the custom parser's output base to label candidate runtime scalar offsets.

The parser does prove the active object contains named fog-map resource references and a named grain-noise reference. It does **not** identify which scalar controls produce the white far-camera bands, show the active scene's current values, or locate the PC renderer code consuming the values. The exact numeric field mapping and reversible Photo-only override remain unresolved; this pass does not justify writes to the object.

## Reproducible RVAs

- Built Atmosphere parser: `0xFAE710`; fog map groups: `0xFAECA9–0xFAED30`; grain-noise group: `0xFAED55–0xFAED90`.
- Default atmosphere initializer: `0xFAF910`.
- Fog-map typed reference helper: `0xFB3D40`; descriptor string RVA `0x32BF470`.
- Film-grain typed reference helper: `0xFB3E80`; descriptor string RVA `0x32BF4B8`.
- Active atmosphere registry lookup: `0xFB1130`.
