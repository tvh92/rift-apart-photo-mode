# Photo fog candidate review

Read-only review of `outputs/camera-native-fog-candidate/PhotoFog.h`, `PhotoLOD.h`, and `GeometryLOD.h` against the local executable's caller and the existing renderer evidence. No source or game files were edited by this review.

## ABI and call site

The 8-byte site at `0x12BD0B0` is an aligned 5-byte `CALL FB66A0` followed by `TEST R14,R14`; replacing only the call preserves the test. The adjacent guard also verifies the upstream `mov rdi,rcx` at `0x12BCE27`.

The full caller setup resolves the register roles: `0x12BCE10` receives the original view in `RCX`, copies it to nonvolatile `RDI`, receives the renderer block in `R8`, and saves it in `R14`. The job clone is placed at `job+0x570`; the renderer block is placed at `job+0x578` (`0x12BCF5E`, `0x12BCF98`). At the target call, `RCX=job`, `RDX=R12`; `FB66A0` immediately moves `RDX` to `R8`, then consumes the renderer block from `job+0x578`. Therefore the relay's `mov R8,RDI` correctly passes the original view as the hook's third argument; my earlier contrary concern was based on misidentifying `RCX`'s role and is retracted. The wrapper calls the original function once with the original two meaningful arguments, `(job, RDX)`.

The generated relay is a leaf tail jump: it changes volatile `R8`, loads the C hook address into volatile `RAX`, then jumps. It leaves the original call's return address and stack alignment intact, adds no frame, and preserves nonvolatile registers. `FB66A0` does not use incoming `R8` as an argument because it overwrites it from `RDX` at entry. Its scratch XMM/register behavior is compatible with an ordinary Windows x64 call wrapper. The supplied native fixture is the right place to assert the relay input (`RDI` view), block pointer (`job+0x578`), and exactly one original call.

## Scope, lifetime, and guards

The hook snapshots from `job+0x578` before the native `FB66A0` call, then lets that original call run. It does not modify the source atmosphere or resolved texture records. It operates only when both pointer checks identify the primary view, the cloned and source-view `+0xF90` values agree, the Photo session gate is active, and the geometry preference is enabled for the per-frame copy. It calls native `FB66A0` even when guards fail. The existing `HookPhotoTick` updates session state on both sides of the native tick, clears it before close/teardown states, and disables the per-frame write when the preference is off. As each renderer block is rebuilt and passed through this helper per frame, off/exit naturally resumes native data on its next invocation.

The snapshot is `0x84` bytes from renderer `+0x110` through `+0x193`. The preparation routine copies `0x8C` bytes from source `+0x3EC..+0x477` into renderer `+0x110..+0x19B` (`0x11D396B..0x11D39E1`). Thus the candidate intentionally/incidentally omits the final 8 bytes, renderer `+0x194..+0x19B` (source `+0x470..+0x477`). In the recorded near/far captures, both corresponding trailing floats at `+0x194/+0x198` are zero, and the reported near-fog-at-far diagnostic succeeded with the shorter block. This is not a blocker for that tested diagnostic, but the boundary should remain explicit: it is a 132-byte numeric prefix, not a complete snapshot of the copied 140-byte fog record. If the implementation is intended to retain the whole record across arbitrary scenes, validate those two tail floats or capture the full `0x8C` bytes.

The installation guard checks the exact 8 call-site bytes and the upstream register instruction before allocating a relay. The exchange uses an aligned 64-bit compare-exchange, suspends other process threads, refuses to patch when a thread IP is inside the 8-byte site, and keeps an uncertain relay alive if rollback state may still reference it. The helper's second patch slot is zero-initialized; its IP-range check cannot match normal user-mode thread IPs. Native tests should cover failed allocation, guard mismatch, failed patch/rollback, off/exit pass-through, and session re-entry reset.

## Review result

I found no remaining ABI or lifecycle blocker after resolving the RDI/R14 roles against the caller. The only review item is the documented prefix-vs-full-record boundary above. The passing near-fog-at-far runtime diagnostic is strong evidence that the captured prefix is sufficient for the reported Corson view; it is not evidence that the omitted tail fields are irrelevant to all scenes or all Photo sessions.
