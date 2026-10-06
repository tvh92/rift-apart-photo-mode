# Native Free Photo Mode camera data flow

Read-only static disassembly of the installed `RiftApart.exe`. The existing `work/disassemble_camera.py` utility parsed PE RVAs and iced_x86 decoded the machine code; no game process was inspected or modified.

## Main result

Free camera configuration is copied into the runtime camera-motion object during the Free camera update/activation path at RVA `0x1A5D4D0` (Free camera vtable slot 12). It looks up the object associated with the `68EBD10` key through the Free camera's `[this+0x10]` context, and writes these data fields directly into that object:

| Free camera data | Runtime motion object | Meaning from generated schema |
|---|---:|---|
| `[this+0xF8]` | `+0x68` | tether distance (passed via helper `0x183E5D0`) |
| `[this+0xFC]` | `+0x6C` | move speed |
| `[this+0x100]` | `+0x84` | rise speed |
| `[this+0x104]` | `+0x70` | acceleration |

The schema names and field order are independently recorded in `work/FreeMoveCamData.cs` (`TetherDistance`, `MoveSpeed`, `RiseSpeed`, `Acceleration`). At `0x1A5D535–0x1A5D563`, the code loads the three float fields and stores them at runtime offsets `+0x6C`, `+0x84`, and `+0x70`. The preceding call at `0x1A5D543` calls helper `0x183E5D0` with the data object obtained from the Free camera's `[this+0xB8]` path and the float at `[this+0xF8]`; that helper writes the float into runtime `+0x68` and sets a related validity flag at `+0x95`.

The motion update at RVA `0x1A5EBA0` reads these runtime values: it uses `+0x6C` in the timestep/speed integration, reads `+0x84` as the rise component, and reads `+0x70` as an acceleration parameter (with a fallback to `+0x90` when `+0x70` is zero). Therefore a refreshed runtime `+0x6C` is the direct movement-speed multiplier path; changing only the source Free camera data has no demonstrated effect until this setup/copy path runs for the active motion object.

## Implication for the reported live values

The reported Free source values (`+0xFC=20`, `+0x100=10`, `+0x104=10000`) should produce runtime `+0x6C=20`, `+0x84=10`, `+0x70=10000` when the above method runs. If a same-session sample of the active MotionFly object instead shows `+0x6C=2`, `+0x84=1`, `+0x70=10000`, that is inconsistent with the direct copies for the first two fields. It points to one of: the copy method has not run since the source edit, the inspected MotionFly instance is not the one reached through this lookup, or another setup path overwrote those fields. Static code alone cannot choose among these runtime explanations.

## Relevant instruction evidence

- `0x1A5D4E5`: call Free camera helper `0x1A5CF10`.
- `0x1A5D4EA–0x1A5D513`: resolve runtime object using `[this+0x10]` and key at `0x68EBD10`.
- `0x1A5D51B–0x1A5D524`: copy Free camera `[this+0x58]` into object `+0x60`, then initialize motion position/velocity with `0x183E570`.
- `0x1A5D529–0x1A5D543`: resolve data at `[this+0xB8]`, pass `[this+0xF8]` to `0x183E5D0`.
- `0x1A5D548–0x1A5D563`: exact stores `+0xFC → +0x6C`, `+0x100 → +0x84`, `+0x104 → +0x70`.
- `0x1A5EBA0–0x1A5ECC2` and `0x1A5EF16–0x1A5EFCF`: update reads speed/acceleration/rise fields and integrates displacement.

This only establishes the config-to-runtime data flow. It does not identify a keyboard binding for the “camera fast” input action.
