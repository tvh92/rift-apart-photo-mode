# Photo Mode effects initialization trace

Read-only trace for executable build 23987138. No game, source, or install files were changed.

## Findings

- The UI option schema does not contain a default-value property. `UIPhotoModeOption` declares ID, label, `ValueMin`, `ValueMax`, fidelity, slider/clamp type, and settings strings. The decoded UI config contains option IDs for color correction blend, vignette, and film grain, with vignette max 10 and implicit min 0; DOF focus distance is 1..180 and FOV is 0.35..2 radians. These are slider bounds, not entry defaults.
- `PhotomodeSystemConfig` also contains no per-effect default values. Consequently, changing UI bounds cannot make the effects start neutral, and no asset-side default field was identified in the preserved schema/config evidence.
- Shared Photo Mode object initialization is at RVA `0x1A58550`. It zero-initializes many object fields and initializes data buffers, but the effect-facing renderer values cannot safely be inferred as neutral values from this constructor: the runtime entry path reads the renderer's current state into a separate snapshot.
- Candidate one-time entry path: RVA `0x1A56D70`. The first instructions require `[this+0x50] == 0` and `[this+0x54] != 0`; otherwise it returns via `0x1A57203`. The constructor above initializes the byte at `+0x54` to zero. On the active branch, the method invokes virtual getters at vtable offsets `+0xF8`, `+0x100`, `+0x108`, `+0x110`, `+0x118`, and `+0x120` and copies their returned values into object fields around `+0x770..+0x7E8` (`0x1A56F06..0x1A57063`). RVA `0x1A58F40` duplicates that snapshot pattern. This is evidence of entry-time state capture, not an effect reset itself.
- The snapshot pattern means a candidate effect initializer should run only after the original state has been captured on the guarded entry path, leaving native controls free to change the live settings afterward. The `0x1A56D70` state/flag guard is a stronger lifecycle candidate than the shared `PreUpdate` callback; do not place repeated zeroing in a per-frame update. I did not identify the exact renderer setter used by each UI option in this bounded trace.
- No specific one-time reset handler for vignette/grain/color correction was established. The string `kPhotomodeReset` and its UI binding show an input exists, but do not prove it resets effect options. Do not treat it as the required reset hook without tracing its consumer. Persistent user-setting storage for these effects was not found in the inspected schema and lifecycle paths; whether values are remembered elsewhere remains open.
- Do not zero FOV or DOF fields as a shortcut. The exposed ranges show FOV and DOF values have valid nonzero domains; zeroing them risks invalid camera/render state. Candidate neutral values are effect-specific (for example vignette intensity and grain strength), and color correction likely requires a blend value or disabling/neutral texture selection rather than blindly clearing all adjacent data.

## Evidence files and RVAs

- `work/UIPhotoModeOption.cs`: option schema; no default member.
- `work/PhotoOptionIds.cs`: effect option identifiers.
- `work/config_00af8d54.json`: decoded slider limits.
- `work/PhotomodeSystemConfig.cs`: native Photo Mode asset schema, no effect defaults.
- `work/lod-photo-vtables.json`: `PhotomodeSystemShared` vtable, including initialization/lifecycle method addresses.
- `work/lod-photo-disassembly.txt`: preserved method disassembly.
- Read-only reproduction using `work/disassemble_camera.py` confirmed RVAs `0x1A58550`, `0x1A56D70`, `0x1A58F40`, `0x1A58E00`, and `0x1A57203`.

## Recommendation

Keep the current entry path as a candidate only. Before implementation, trace the native UI option consumer to establish the live fields/setters for vignette intensity, center clear, film grain size/strength, and color correction blend. Then apply neutral values once after the entry snapshot, and separately locate a real reset path if reset should reapply them. Preserve the snapshot so Photo Mode exit can restore the original renderer values.
