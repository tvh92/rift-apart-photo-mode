# Photo Mode UI RTTI follow-up

Read-only RTTI/vtable and method trace for executable build 23987138. No game/source/install files changed.

## RTTI classes and vtables

The executable has distinct native RTTI names for `UIPhotoModeOption`, `ScreenUIElementPhotoModeOptions@GUI2`, `UIPhotoModeOptionsPage`, and `UIPhotoModeConfig`. Their recovered COL/vtable RVAs are:

| Class | COL RVA | vtable RVA |
|---|---:|---:|
| `UIPhotoModeOption` | `0x4B05120` | `0x3145830` |
| `ScreenUIElementPhotoModeOptions@GUI2` | `0x4A81448` | `0x2F13150` |
| `UIPhotoModeOptionsPage` | `0x4B05198` | `0x31458A0` |
| `UIPhotoModeConfig` | `0x4B05300` | `0x31459F0` |

The `UIPhotoModeOption` vtable has 13 executable methods before its next RTTI locator: `0xC86DB0, 0xC87290, 0xC863F0, 0xC868D0, 0xC85230, 0xC87AC0, 0xC87D50, 0xC87770, 0xC88470, 0xC8A3C0, 0xC8E9D0, 0xC84740, 0xC79B20`. The terminal method at `0xC79B20` installs the class vtable and conditionally deletes a `0x48`-byte object, so it is a deleting-destructor path. This class vtable did not expose a numeric option dispatch or an effect setter.

## UI method checks

- Screen UI vtable `0x2F13150` includes methods `0x170D280`, `0x170D580`, `0x170D4E0`, `0x635FD0`, `0x635170`, and `0x635150` (slots 7, 11, 12, 19, 21, 22 respectively).
- `0x170D280` is a UI-side staging/update method. Its arguments are an index (`edx`) and a group (`r8d`, accepted range 0..3); it indexes an array of `0x638`-byte group records with indices through `0x2C`, and updates per-entry values/flags. It does not switch on Photo option IDs 10..13 and does not write the known renderer/global targets.
- `0x170D4E0` and `0x170D580` manage the UI/cohtml option object; no numeric Photo option dispatch is present.
- `0x635FD0` is a large zero/default initializer for the screen UI object, with broad UI/list state fields. It does not initialize vignette/grain renderer state.
- `0x635150` is a small guard/jump to `0x1A5AED0`; `0x635170` is a screen lifecycle/update routine that resolves option/list objects and forwards callbacks. No direct effect field setter was established in the inspected paths.

The Photo option enum order maps 10=`VignetteIntensity`, 11=`VignetteCenterClear`, 12=`FilmGrainSize`, 13=`FilmGrainStrength`; the inspected option data vtable and screen UI methods contain no switch/table resolving those values to `renderer+0x388/+0x38C` or global `0x53391B8`. This follow-up therefore narrows the likely setter away from the RTTI `UIPhotoModeOption` data class and UI-side staging method, but still does not prove effect semantics or a safe neutral field.

## Reproduction

- `work/effects-continuation-luna-rtti.py` is a read-only PE RTTI/COL/vtable enumerator created for this trace.
- `work/disassemble_camera.py` decoded the bounded methods listed above using local iced_x86 support.
- `work/PhotoOptionIds.cs` provides the DDL enum ordering and names.
