# Collision trace continuation (Luna)

Target executable: `C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\RiftApart.exe`, SHA-256 `51299faca61866cf10ea9035a15b8f22600a56557dd5ffc1aad390d5a54e6d82` (the supported build listed in the workspace handoff). Analysis used the existing `work/disassemble_camera.py`, `work/rip-refs.bin`, and schema/config artifacts. No game, install, or shared source files were modified.

## Finding

The native Free Photo camera movement routine contains a swept world collision query followed by a hit-response branch. This is the demonstrated camera blocking path. `CamCollisRad` is present in the schema and executable reflection data, but its dedicated native consumer was not resolved to an instruction path. Consequently, setting it to zero is not established as disabling collision. The movement query has a live call and hit-response branch that do not test this config field in the routine examined; zero could at most affect some separate query parameter/shape consumer unless further evidence shows the field reaches this path. It should not be treated as a no-clip flag.

## Verified path

- Camera movement updater: `PhotomodeCameraMotionFly::UpdateMiddle(float)`, RVA bounds `[0x1A5EBA0, 0x1A5F364)`. This name is in `work/exe-photo-strings.json`; the current workspace handoff identifies the motion update as vtable slot 10.
- Query descriptor setup at `0x1A5F146`: `mov edx,3; lea rcx,[rbp-40h]; call 0x118F070`. The callee initializes a fixed query descriptor using type index 3 from a table at `0x64FE370`.
- Endpoints and query call: `0x1A5F1C7` sets the query vtable pointer `0x45FDF70`; `0x1A5F1D3` supplies the candidate endpoint in `r9`; `0x1A5F1D8` supplies current position in `r8`; `0x1A5F1E0` loads the query context from global `0x53355F0`; `0x1A5F1E7` calls `0x11B9C30`. The latter is a thunk that transfers to `0x11AA050`.
- Exact bytes at `0x1A5F1E7`: `E8 44 AA 75 FF 84 C0 74 3B`. The call returns hit status in `AL`; `test al,al` is at `0x1A5F1EC`; `je 0x1A5F22B` is at `0x1A5F1EE` (`74 3B`). A hit falls through into correction code at `0x1A5F1F0–0x1A5F22A`; a miss jumps to cleanup at `0x1A5F22B`.
- Cleanup at `0x1A5F22B` calls `0x1195750`. Separate camera bounds/config processing resumes at `0x1A5F234`; the selected position is stored at `0x1A5F2FA` and the function returns at `0x1A5F364`.

The conditional branch is a narrow possible no-block point: changing `74 3B` to `EB 3B` at `0x1A5F1EE` would always skip only the hit-response block, continue through query cleanup, and keep the later camera processing. The query still executes, so this would avoid the position correction rather than eliminate raycast cost. This is static control-flow analysis only; it is not a tested patch. A method clone or guarded code hook is preferable to a process-wide text patch if this fallback is pursued.

## `CamCollisRad` evidence and limit

- Schema: `work/PhotomodeSystemConfig.cs` registers float hash `0x3B89FD7D` with default `0.20f`. The decoded asset `work/config_00a54140.json` does not serialize a `CamCollisRad` member, so the decoded asset does not establish an authored override.
- In the executable the field hash occurs once at file offset `0x3170508` (RVA `0x3171308`) and the name occurs once at file offset `0x31706D8` (RVA `0x31714D8`), in the DDL/reflection metadata area. The prebuilt RIP-relative reference index has no direct code xref to either address.
- The movement updater above does not read a field identifiable as `CamCollisRad`, nor does it test a zero-radius sentinel before its query. Setup at `0x1A5D4D0` sends `FreeMoveCamData +0xF8` to motion-controller `+0x68`; `UpdateMiddle` uses `+0x68` as a distance/tether threshold. That is separate from `CamCollisRad`.

Therefore: the actual blocking query path is verified; the field-specific consumer and any effect of zero on its query thickness remain unresolved. A zero radius could still leave a ray/degenerate query, and the verified movement query/correction path makes “zero means collision off” unsupported.

## Clone/unwind and call-site scope review

The exact PE runtime-function record is `(Begin=0x1A5EBA0, End=0x1A5F364, UnwindData=0x4F1570C)`. Its UNWIND_INFO is version 1, flags 2 (`UNW_FLAG_UHANDLER`), prolog size `0x3E`, with 23 unwind-code slots. Handler RVA `0x2D27AB7` jumps through IAT slot `0x2E38248`, whose import name is `__CxxFrameHandler4` (import-name bytes at RVA `0x512ADB8`). Handler-specific FuncInfo4 data follows at RVA `0x4F15748`.

A clone cannot safely rely on displacement relocation alone. It would need a registered dynamic function table and correctly based unwind metadata. Since FuncInfo4 encodes function ranges used by C++ exception handling, a cloned function also needs those references adapted to the clone. Copying or reusing the original unwind record risks wrong exception dispatch, cleanup, and stack walks. The instruction scan found direct relative calls and RIP-relative data accesses, no indirect CALL/JMP within the method body; identical-length copying preserves internal relative branches, but all rel32 calls and RIP disp32 accesses still require relocation.

The function pointer occurs once in executable data: vtable slot 10 at `0x45FDF40 = 0x45FDEF0 + 8*10`, under RTTI type `.?AVPhotomodeCameraMotionFly@Camera2@@` (`work/camera-rtti.json`). The sole indexed direct caller is `0x1A5F404` in `[0x1A5F3C1, 0x1A5F41E)`, a collection loop that calls the method conditionally. The embedded function-name string also identifies `Camera2::PhotomodeCameraMotionFly::UpdateMiddle(float)`. Static evidence supports a Photo-specific class path and found no non-Photo caller; because the direct caller is a dispatcher, runtime owner/type matching is still the stronger guard.

This supports the simpler guarded one-byte original-code change: at `0x1A5F1EE`, verify `84 C0 74 3B` then CAS only `74` to `EB`; restore only `EB` to `74` on disable after symmetric verification. Preserve the original function and unwind metadata, keep the relative offset byte unchanged, and flush the instruction cache after each change. Concurrently executing updates may observe either old or new behavior for one frame. The raycast still runs and its cleanup plus later constraints remain intact. This is static design review, not a runtime test.
