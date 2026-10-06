# Built Atmosphere native loader trace

Read-only trace of local executable build 23987138, following the indexed `Atmosphere Built File` record type `0x21D5E72C` and its `0x02F06D4E` section. No source, executable, game data, or installed files were changed. The trace confirms a concrete native parser and its output object, but does not name the base-section fields as fog values.

## Entry and type validation

The executable has one `.text` occurrence of type hash `0x21D5E72C`, at RVA `0xFAE73F`; the containing function begins at `0xFAE710`. It validates the asset through `0xFA2B70`, passing the type hash and descriptor/string pointer `0x32BD6E0`. `0xFA2B70` performs `cmp [rdx+4],r8d; sete al`, so the type-hash match is directly confirmed. The referenced string is `kBuiltAtmosphereBaseVersion: 229-tarciuolo: Separate embedded texels to a second section, kBuiltTexturePDDVersion: 93-rsprentall: Remove compression of streamed mips`.

`0x15B3220` performs a binary search over the asset section table; at `0xFAE758`, the loader asks it for section tag `0x02F06D4E`. On success, it reads that section's relative data offset from `[section+4]`, adds the file base, and uses the result as `rsi`, the source block for the main decode. The indexed records report this same section tag with a length of `0x708` for typical atmosphere assets.

## What the loader materializes

The function copies/decodes fields from the `0x02F06D4E` source block into an output object based at `rdi`. Direct loads span source offsets beginning around `+0x20` through at least `+0x4A8`; target members span `rdi+0x30` through `rdi+0x688`, with typed helper calls including `0xFB3F20`, `0xFB3CA0`, `0xFB3E30`, `0xFB3AD0`, `0xFB3CF0`, `0xFB3C00`, `0xFB3D40`, `0xFB3E80`, `0xFB3C50`, `0xFB4060`, `0xFB3D90`, `0xFB3DE0`, and `0xFB3BB0`. This proves that `0x02F06D4E` is a concrete built-atmosphere base payload consumed by native code, rather than generic DDL configuration.

The loader also handles separate named/reference blocks:

- It converts the base-block reference at source `+0x3C` using the label string `CloudCover` at RVA `0x32BEB38` and stores the resulting pointer at output `+0xF0`. Later it queries tag `0xC438B59C` at `0xFAF04C` and processes its entries.
- It queries tag `0xE7997256` at `0xFAEDFE` for embedded texel data. This agrees with the version string's statement that embedded texels are in a second section. Its large payload is treated as texture data, not a fog settings block.
- It queries tag `0x71C168B4` at `0xFAF0B3`. The loader uses descriptor string `Atmosphere IBL Lights` at RVA `0x32BEB48` and populates an output array/count at `rdi+0x140/+0x148`.
- Nearby descriptor strings include `Light Grid Atmosphere` at `0x32BEAE8` and `Atmosphere LightGridModConfig` at `0x32BEB00`, used by helper calls within the base-section conversion.

## Connection to Photo Mode's current-atmosphere block

A separate Photo trace confirms the parser output is the same in-memory atmosphere object exposed through the current-atmosphere registry. `0xFAE1A0` returns global object address `0x6240400`; companion `0xFAE1B0` passes that same object to initializer `0xFAF910`. The initializer uses descriptor string `Default Atmosphere` at `0x32BEB20` and initializes the same member layout populated by `0xFAE710` (including ranges through the `+0x688` members).

`0xFB1130` with index `edx=0` returns `[registry+0x1C8]`. Photo getters such as `0x1A57D40`, `0x1A57D70`, `0x1A57DA0`, `0x1A57DD0`, `0x1A57E80`, and `0x1A57EB0` call that lookup on registry `0x52DDA20`; if it returns null, they use `0xFAE1A0`, then return the same block plus `0x300`, `0xF8`, `0x4C0`, `0x3EC`, `0xA8`, and `0x524`, respectively. Photo exit `0x1A57560` also obtains registry slot 0 through `0xFB1130` and restores two 32-bit values at block `+0x388/+0x38C` and another pair at `+0x3D8/+0x3DC`. The built-file decoder writes the overlapping destination members `+0x388` from source `+0x318` and `+0x3D8` from source `+0x368`, confirming shared object layout.

This proves that built-atmosphere decoding materializes the registry object Photo Mode accesses. It still does not name `+0x388` or `+0x3D8` as fog fields, nor identify a decoder destination offset corresponding to `FogSettingsDef` or volumetric distances. Treat these offsets as shared atmosphere state with unresolved semantics; do not use them as fog controls or override them from a Photo loop.

## Fog mapping and limits

This is the first confirmed link from the custom `Atmosphere Built File` format to a native in-memory atmosphere object. It does not yet map any `0x02F06D4E` source offset to `FogSettingsDef.ColorMapDepthRange`, `ColorMapDepthScale`, `VolumetricFogSettingsDef.NearDistance`, or `FarDistance`. The function uses a custom packed built-file layout and unlabeled destination offsets; applying the public DDL reflection offsets directly to its `0x708` section would be unverified.

The 95-entry Corson/Nefarious archive inventory remains in `work/corson-v-atmosphere-asset-index.md`. That index found no Corson/Emperor/city path in the indexed `d\\atmosphere` assets, and only Neo_Nefarious sky-texture paths. Thus this loader trace identifies the runtime decoder but not which asset is active near the Emperor statue, nor the values responsible for the pale bands. A remaining proof step is a native field name/layout mapping for the `0x02F06D4E` base payload plus an active scene asset reference; no field write or renderer patch is justified yet.

## Reproducible RVAs

- Type dispatch hash `0x21D5E72C`: `0xFAE73F`.
- Main parser entry: `0xFAE710`.
- Required base payload tag `0x02F06D4E`: query at `0xFAE758`.
- Embedded texel tag `0xE7997256`: query at `0xFAEDFE`.
- IBL-light tag `0x71C168B4`: query at `0xFAF0B3`.
- Cloud-cover data tag `0xC438B59C`: query at `0xFAF04C`.
- Built Atmosphere version descriptor: `0x32BD6E0`.
