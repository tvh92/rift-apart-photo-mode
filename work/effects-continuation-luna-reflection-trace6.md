# Photo Mode effect reflection and dispatch trace

Read-only analysis of executable build 23987138. No game, native source, or installation files were changed. This trace follows the requested PhotoModeSystem methods and native DDL reflection records. It proves named post-processing field layouts, but does **not** prove that any of those DDL objects are the Photo Mode embedded blocks or identify the slider-to-renderer setter.

## Requested PhotoModeSystem methods

The main-vtable entries at `0x8DD600`, `0x8DD5D0`, `0x8DD5C0`, `0x8DD610`, `0x8DD5F0`, and `0x8DD5E0` are direct embedded-block getters. They return `this+0xAC4`, `this+0xB0C`, `this+0xB38`, `this+0xBA8`, `this+0xBC4`, and `this+0xC50`, respectively. The next method `0x8DDED0` checks whether the engine-global `+0x37FD0` equals 2; it is a predicate, not an effect setter.

The requested methods `0x8DE720` and `0x8DF1A0` do not dispatch slider IDs to native effect fields:

- `0x8DE720` initializes Photo Mode UI/config state. It resolves DDL values and setting objects, registers hashes through `0x8E5900` / `0x10DE850`, and initializes system flags and arrays. No comparisons against `VignetteIntensity`, `VignetteCenterClear`, `FilmGrainSize`, or `FilmGrainStrength` lead to writes into the renderer effect blocks.
- `0x8DF1A0` enumerates DDL setting lists, derives each field hash from the DDL object header, and calls `0x8E3210` with the hash and a zero scalar. `0x8E3210` is a generic setting/UI availability update path; it clamps/quantizes its scalar and changes setting/UI state. The traced caller and callee do not write an identified renderer effect field.
- `0x8DF010` transitions the system lifecycle state to `0x0B` via `0x1A5AB40`.
- `0x8DF710` transitions the lifecycle state to `0x0E` and refreshes a global predicate.
- `0x8DF810` is a short state-transition thunk beginning with `mov edx,9`; it does not contain an effect-field write.
- `0x8DE5A0` returns a global byte at `global+0x4F0`.
- `0x8E4F00` validates the current option/list index against a child count; it is a predicate, not a setter.

This is consistent with the earlier correction: `[PhotomodeSystem+0x50]` is lifecycle state (constructor default `0x0E`), not a numeric PhotoOption ID. No state ordinal is mapped to a vignette or grain control here.

## Named post-processing DDL fields found in native reflection metadata

The executable contains reflection records for `VignetteSettingsDef`, `FilmGrainSettingsDef`, and `ColorCorrectionSettingsDef`. Their field-name tables and per-field offset tables are adjacent to the corresponding type records. These are native engine post-processing settings types; the records do not identify which PhotoModeSystem block, if any, contains each type.

| Type | Native metadata record (file offset / RVA) | Reflected members | Reflected data offsets | Type size |
|---|---:|---|---|---:|
| `VignetteSettingsDef` | `0x54AA630` / `0x54AB830` | `Enabled`, `Intensity`, `CenterClear` | `+0x20`, `+0x24`, `+0x28` | `0x30` |
| `FilmGrainSettingsDef` | `0x54AAB30` / `0x54ABD30` | `Enabled`, `Size`, `Strength`, `SizeAt4K`, `StrengthAt4K`, `NoiseTexture` | offset table contains `+0x20` through `+0x40`; likely member offsets include `+0x20`, `+0x24`, `+0x28`, `+0x30`, `+0x34`, `+0x38` | `0x50` |
| `ColorCorrectionSettingsDef` | `0x54AAC70` / `0x54ABE70` | `Enabled`, `SourcePath` | not assigned to UI `ColorCorrectionTexture` or `ColorCorrectionBlend` by this trace | `0x40` |

The `VignetteSettingsDef` record’s offset array at file offset `0x44D741C` explicitly contains the data offsets `0x20`, `0x24`, and `0x28`, and its field-name table identifies those members in order. Its initializer at RVA `0x13E7980` clears qwords at `this+0x20` and `this+0x28` as well as the preceding object storage. That establishes zero-initialized vignette `Intensity` and `CenterClear` for this DDL type. The same initializer is consistent with `Enabled=false`.

For `FilmGrainSettingsDef`, the name table at file offset `0x44DBEC8` identifies the members above. The field-offset table at `0x44DC0C4` contains a larger sequence than the six named members, so this report does not claim an exact one-to-one mapping for every grain field without decoding its inherited/auxiliary entries. The native initializer at RVA `0x13E8FC0` clears object header qwords and invokes a nested initializer at `this+0x38`; it does not explicitly assign the scalar grain values. Therefore the constructor alone is not evidence for zero `Size` or `Strength`.

## UI config and effect setter result

`work/config_00af8d54.json` has `VignetteIntensity`, `VignetteCenterClear`, `FilmGrainSize`, and `FilmGrainStrength` entries under `PHOTO_CATEGORY_EFFECTS`. The slider entries provide labels and, for vignette intensity, `ValueMax=10`; none provides a `Settings` list that names a renderer property or an initial default. The generated `UIPhotoModeOption` schema only defines ID, label, min/max, fidelity, slider/clamp type, and settings labels.

The requested methods plus UI config metadata do not expose a proven numeric-ID setter dispatch. The direct renderer getters previously traced at `0x1A57D40/0x1A57D70/0x1A57DA0/0x1A57DD0/0x1A57E80/0x1A57EB0` expose renderer blocks at `+0x300/+0xF8/+0x4C0/+0x3EC/+0xA8/+0x524`, but no correspondence from those blocks to the DDL reflection records was found here.

## Consequence for an entry/reset hook

The vignette DDL layout provides a concrete neutral representation (`Intensity=0` at `+0x24`) for an object proven to be `VignetteSettingsDef`. It does not establish that Photo Mode’s `this+0xAC4..+0xC50` or the six renderer blocks are instances of that type, nor that writing this DDL object changes the renderer. The grain object mapping is less complete. The safe one-time Photo Mode entry point remains structurally interesting because entry snapshots values and exit restores them, but no effect-specific address is proven by this trace. Do not install a zero write at an unlabeled block; do not repeatedly override slider values; and do not zero FOV or DOF fields.

## Reproduction

- `work/disassemble_camera.py` decoded the requested bounded functions and the two native DDL initializer functions; the iced_x86 import required the explicitly authorized read-only elevated invocation.
- A read-only PE metadata scan mapped the four DDL type-name strings to their adjacent reflection records and followed field-name/offset tables.
- `work/UIPhotoModeOption.cs`, `work/PhotoOptionIds.cs`, and `work/config_00af8d54.json` provide the schema and UI option evidence.
