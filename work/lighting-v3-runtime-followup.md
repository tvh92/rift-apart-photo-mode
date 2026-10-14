# Lighting-v3 runtime follow-up, 6 October 2026

User reports partial lighting improvement, flicker at large distances, poor response to Ctrl, and some nearby lights disappearing with detail OFF. Sargasso crashes high in the sky with **Ctrl ON** (confirmed); user also wants airborne dust filtered. All remain open issues. Installed v3 SHA256 is `c4be06b9e069829ba3c173ab3545353f38de04d6a98c5f58533af42ae9efbe66`. No DLL, assets, INI, graphics settings, saves or live process were changed in this investigation.

## Crash evidence

Two saved dumps, 13:33:46 and 13:35:39 local, embed exactly:

`[nri(D3D12)::ERROR] -- ID3D12Resource::Map() failed, error code: 0x887A0005.`

Exception 0x80000003 is at KERNELBASE.dll+0xE95A2; the first exception-stack word maps to NRI.dll+0x5DD2 in both dumps. These words are candidates, not a symbolically unwound call stack. The breakpoint/pure-virtual-call log is insufficient to identify the original failure.

Windows System events: Display 4101 at 13:33:50 and 13:35:39 says the NVIDIA display driver stopped responding and recovered; nvlddmkm 153 entries precede them. The dump HRESULT identifies graphics device loss (`DXGI_ERROR_DEVICE_REMOVED`). It does not supply the detailed reason or identify geometry, lights, ray tracing, dust, memory pressure, a driver defect or a camera boundary as the cause. No GetDeviceRemovedReason or DRED breadcrumbs were recovered. Do not add a speculative height clamp, increase GPU limits, disable device-loss handling, or change TDR registry settings on this evidence.

The crash-session log records 2560x1440, DLAA, no upscaler, Very High RT reflections/shadows/AO, Ultra textures, Very High LOD and particle lighting. RTX 3060 reports 12115 MB dedicated VRAM. Free system RAM at crash was about 1.2 GB. These describe the workload, not proof of overload or allocation failure. The current proxy log only contains unsupported-executable forwarding lines and is not a game-session hook log.

Saved evidence: `sargasso-crash-readonly-summary.json`, `sargasso-display-events.json`; decoder `inspect_game_minidump.py` reads bounded saved files only. Original dumps and game logs remain at their original paths and are not copied into the repository. Eight malformed-file/error-extraction tests pass.

Official HRESULT reference: https://learn.microsoft.com/en-us/windows/win32/direct3ddxgi/dxgi-error

Potential further GPU evidence: https://learn.microsoft.com/en-us/windows/win32/direct3d12/use-dred (requires configuration before device creation; no DRED instrumentation installed).

## Lighting diagnosis and corrected observer

Combined Ctrl behavior is intentional: OFF restores native geometry/light/fog rules. That does not explain the nearby-light defect. The three GetAsyncKeyState reads and asynchronous shared gate remain candidate timing concerns, not diagnosed causes; changing a key poll alone would not establish a lighting fix.

`light-query-reuse-toggle-response-readonly.md` refutes stale query reuse for all three indexed direct frame callers: they fail the native reuse prerequisites, so build fresh queries. Do not patch cache invalidation on this evidence. `lighting-toggle-flicker-readonly-review.md` documents native filters still present and the need to identify where a particular light disappears.

Corrected `capture_photo_lights_readonly.py`: request slot+68 may still name a raw gather allocation after 10BB270 replaces query+8 and rewrites query+10. Therefore current query count cannot bound the old allocation. Worker output is now metadata only, never dereferenced. Current query arrays retain their native count/owner/key/stability guards; query ownership is revalidated immediately before arrays. Tests cover unreadable/retired worker buffers and ownership changes at the read boundary. **31 isolated tests pass.** Earlier raw captures are preserved and any old worker-output interpretations are superseded; their current-query and submitted-record observations are distinct from that wrong-count path.

The reader now supports up to 32 samples over a bounded 10 seconds, with timestamp and observer hash. Next concrete capture, at normal height beside a light that disappears with Ctrl OFF:

1. Hold the camera still with the light visible, Ctrl ON: `python work/capture_photo_lights_readonly.py PID --label nearby-on --seconds 10 --samples 32 --interval-ms 250`.
2. Keep the camera and framing unchanged; toggle OFF. Capture label `nearby-off` with the same arguments, noting whether the illuminated patch disappears. If an ON capture fails query ownership checks, do not weaken them; report the failed stage.
3. Toggle ON at the same position and capture `nearby-on-return`. Compare source identity/position, current input membership, selected membership and pass67 submitted brightness. Each accepted query/queue has internal rereads; this external capture does not prove one atomic render frame or measure shader/GPU output.

No Sargasso high-altitude crash reproduction is needed for this lighting capture. All process access is QUERY_LIMITED_INFORMATION | VM_READ; no code injection or process writes.

## Dust

`sargasso-dust-readonly-review.md` proves a reflected WeatherDef.Particles configuration and weather-particle shader buffers, but no producer/callsite or Sargasso active dust identity. Individual floating specks may use weather particles or local VFX; broad haze may be fog. No blanket weather/fog/particle suppression is justified yet. Confirm which visible effect the user means and trace the actual primary-view draw before proposing a Photo-only filter. Preserve the confirmed dark-pit fog.
