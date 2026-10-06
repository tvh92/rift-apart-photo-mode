# Lighting, fog, and particle distance fields

Bounded, read-only schema/reflection trace for executable build 23987138. No game, native source, or installation files were changed. The observed behaviors to investigate are missing illumination on nearby surfaces as the Photo Mode camera moves away, and fog in deep pits turning bright white. This report identifies data fields whose documented semantics could explain distance-dependent behavior; it does not claim a renderer consumer, live value, or Photo-only path unless noted.

## Fog and atmosphere fields

Native DDL reflection identifies `AtmosphereDef` (record RVA `0x5D4AD10`, type size `0xFE0`) with child settings at these object offsets:

| AtmosphereDef member | Offset |
|---|---:|
| `EnvLighting` | `+0x208` |
| `FogSettings` | `+0x4B8` |
| `VolumetricFogSettings` | `+0x588` |
| `FilmGrainSettings` | `+0x670` |

`FogSettingsDef` (record RVA `0x54AB470`, size `0xD0`) exposes a height/opacity profile and distance-sensitive color-map controls:

| Field | Offset | Reflection description |
|---|---:|---|
| `ColorMapDepthRange` | `+0x58` | Distance at which fog transitions to the highest mip of the color texture |
| `ColorMapDepthScale` | `+0x5C` | Controls the rate at which fog color transitions mips |
| `NearRadius` | `+0x98` | Description is absent in the native metadata |
| `Height0` / `Opacity0` through `Height4` / `Opacity4` | `+0x9C` through `+0xC0` | Authored height/opacity curve, displayed as bottom, intermediate, and top heights with opacity labels |
| `RemapStrength` / `RemapKeyOpacity` | `+0xC4` / `+0xC8` | Displayed as S-curve strength/center |

This is a plausible candidate for the reported far-camera white fog if the active fog color texture’s high mip or authored height/opacity profile resolves to a pale color. The field description establishes mip transition behavior, but the asset, texture, active value, and render consumer have not been identified.

`VolumetricFogSettingsDef` (record RVA `0x54AB5B0`, size `0x88`) exposes:

| Field | Offset | Reflection description |
|---|---:|---|
| `NearDistance` | `+0x64` | Distance near the camera with no volumetric fog |
| `FarDistance` | `+0x68` | Replace height fog with volumetric fog up to this distance |
| `SunLightScale` | `+0x6C` | Contribution of direct sun/moon light |
| `LightsScale` | `+0x70` | Contribution of dynamic lights |
| `GIScale` | `+0x74` | Contribution of light grids |
| `NoiseVSpeed`, `NoiseSpeed`, `NoiseScale` | `+0x78`, `+0x7C`, `+0x80` | Volumetric fog noise controls |

The descriptions specifically make `NearDistance` and `FarDistance` camera-distance transition controls. That makes them the strongest schema-level candidates for the pit fog changing when the Photo camera moves far away. No native callsite or active atmosphere asset is tied to these members in this trace, so they are not yet a safe hook or override target.

## Environment lighting and shadow-distance fields

`EnvLightingDef` (record RVA `0x54AB0B0`, size `0x128`) contains:

| Field | Offset | Meaning from reflection metadata |
|---|---:|---|
| `ShadowDrawDist` | `+0x6C` | No more specific description present |
| `CsmLodCount` | `+0x70` | Shadow cascade count |
| `FarLodCaching` | `+0x71` | Far CSM LOD contains only static casters and updates only when needed |
| `FarLodTransitionDist` | `+0x74` | Nonzero value selects the CSM far-LOD transition distance; zero uses `Render.CsmFarLodTransitionDist` |
| `FarLodPerfModeOpts` | `+0x78` | Performance mode can move the far-LOD transition closer and remove a CSM LOD |
| `VFXLightMultiplier` | `+0xEC` | Multiplier applied to lights spawned by VFX |

These establish separate shadow, cached-far-LOD, and VFX-light controls. None is proven to govern general direct-light surface illumination. The native `MaxCulledLightDistance` string belongs to a vehicle config cluster: its description says a vehicle’s lights are enabled only within this distance when the vehicle itself is culled from drawing. It should not be treated as a global environment-light range.

The `SetBypassDistantLightingActionPrius` native type is present (type-name string RVA `0x433CE98`, reflection record RVA `0x54F3D70`) and its reflected member is `ActionType`. This trace did not identify a renderer reader or consumer. Its runtime path is being investigated separately by the LOD consumer trace.

## Particles and exhaust distinction

`WeatherDef` has a `Particles` child at `+0xA8`; its child type is `ParticlesDef` (record RVA `0x54AC870`, size `0xA0`). `ParticlesDef` includes:

| Field | Offset | Reflection description |
|---|---:|---|
| `NearFadeDistance` | `+0x40` | Particles fade when closer to the camera than this distance |
| `MaxDrawDistance` | `+0x44` | Particles fade when farther from the camera than this distance |

The remaining reflected fields cover texture, density, speed, size, alpha, color, and weather-oriented controls. This is concrete evidence for weather particle distance fading; no evidence ties it to vehicle exhaust or the observed general geometry changes. Exhaust remains a separate possible VFX/effect-variant path.

## Photo Mode light fields are a separate system

`DefaultPhotoLightSettings` (record RVA `0x5210800`, size `0x50`) has `DefaultRange` alongside intensity, cone angle, softness, shadow enable, and color. The decoded Photo Mode system config sets `DefaultRange=10`. These fields configure user-added Photo Mode lights; they are not evidence for the reach or visibility culling of world lights. The Photo UI’s `LightDistance` option similarly controls a placed Photo light.

## Limits and next evidence needed

This trace found no native render callsite consuming `FogSettingsDef.ColorMapDepthRange`, `VolumetricFogSettingsDef.FarDistance`, or `EnvLightingDef.ShadowDrawDist`, and no active atmosphere asset/value that can be safely changed. The next proof needed is a runtime consumer that reads the atmosphere data using the active Photo camera, plus an asset/value or controlled runtime read showing which field changes at the symptom location. Until that link is established, treat the fog fields as targeted hypotheses, not write targets. The direct-light culling investigation is separate; vehicle `MaxCulledLightDistance` and the Photo light range should not be used to explain missing world illumination without a demonstrated path.

## Reproduction sources

- Native executable reflection records and embedded field strings in `RiftApart.exe`, mapped with the existing read-only PE helper logic.
- `work/rivet-tree.json` lists the corresponding generated schema types (`AtmosphereDef`, `FogSettingsDef`, `VolumetricFogSettingsDef`, `EnvLightingDef`, `WeatherDef`, `ParticlesDef`, and Photo light types).
- `work/lod-strings.json` contains the vehicle-only `MaxCulledLightDistance` description and `MaxCulledFxDistance` companion entry.
- `work/config_00a54140.json` supplies the decoded `DefaultPhotoLightSettings.DefaultRange=10` value.
