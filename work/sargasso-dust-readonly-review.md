# Sargasso airborne dust: bounded offline source review

Date: 6 October 2026. Read-only inspection of local game build 23987138 (`RiftApart.exe` SHA256 `51299faca61866cf10ea9035a15b8f22600a56557dd5ffc1aad390d5a54e6d82`). No game process, assets, source, or installation were changed.

## Evidence for a weather-particle path

- Native DDL reflection in `lighting-effects-lightcull.md` identifies `WeatherDef.Particles` at parent offset `+0xA8`, type `ParticlesDef` (record RVA `0x54AC870`, size `0xA0`). Its `NearFadeDistance` (`+0x40`) and `MaxDrawDistance` (`+0x44`) are documented as particle fade distances. The same reflection includes visual/density controls such as texture, density, size, alpha, and color. This proves a weather-particle configuration type exists; it does not identify Sargasso's active asset or make those reflected offsets applicable to built atmosphere/archive records.
- Shader reflection outputs `shader-fog-reflection-main.txt` and `shader-fog-reflection-main.json` identify `WeatherParticlesAttributesCBuffer` (352 bytes) and `WeatherParticlesCellsCBuffer` (64 bytes). The 352-byte attributes buffer has named fields including `m_Color` at `+0xE0`, `m_NearFade` at `+0x100`, `m_InvDrawDistance` at `+0x104`, `m_Radius` at `+0x108`, `m_Count` at `+0x110`, and `m_LightVolumeGpuId` at `+0x140`. `shader-light-reflection-main.txt` independently lists the two weather-particle buffers and the light-volume field. The reflected names/sizes establish shader-side data layouts, not the CPU upload function, buffer identity at runtime, or whether Sargasso dust uses this shader.
- Executable render-name extraction `fog-light-render-names-main.txt` has a `WeatherBlocker` description at string RVA `0x44F9370`: weather particles and wetness can be blocked in those volumes with an edge fade. This is affirmative engine evidence for a weather-particle subsystem and a volume-based blocker feature; it is not a Photo Mode control or evidence that ambient Sargasso dust is categorized as weather particles.

## Producer/callsite result

The existing `render-pass-registration-main.txt` contains no `WeatherParticles`/weather-particle registration match. The inspected extracted executable string list (`exe-photo-strings.json`) likewise has no weather-particle CBuffer or pass label; the weather-specific render-name evidence above is only the `WeatherBlocker` volume description. The existing shader reflection records do not contain a CPU producer RVA, render-pass callback, upload routine, or call chain from `WeatherDef.Particles` to either buffer. Therefore this bounded pass does not identify a supported native callsite or a concrete Photo-only intervention point.

`m_Count` is an attractive shader-side discriminator by name, but directly changing it is not justified: no evidence ties a particular native upload to the ambient dust, shows it is per-view/per-draw, or proves a Photo-state guard can isolate it from rain/other weather. Setting weather counts or alpha globally could remove unrelated effects. Do not patch DDL offsets in built assets, change global weather settings, or affect confirmed volumetric fog.

## Narrow next diagnostic

1. In a controlled Sargasso Photo Mode reproduction with visible dust, identify the active weather-particle draw/shader and its bound 352-byte attributes and 64-byte cells buffers. Record the buffer contents/read-only identifiers and their producer/callback chain; compare with dust absent or a different view only if available.
2. Trace the producer back to the active `WeatherDef.Particles` instance or another emitter source. If the dust uses a VFX/local-emitter path, stop treating it as weather and identify that emitter/effect ID before considering a filter.
3. Only after the path is tied to the observed dust, establish whether that producer is called for the primary Photo view and whether a Photo-state/Ctrl guard can modify a private per-view/per-draw count or alpha while leaving native state and fog intact. Otherwise there is no justified Photo-only filter.

The runtime association between Sargasso dust and weather particles, exact producer/callsite, active settings/asset, and isolated Photo-only guard all remain unresolved.
