# Fading Photo Mode status candidate

User feedback on the previous lighting buildfa3: illumination appears to remain to a farther distance, but lights still disappear. Keep this result marked as partial. Startup/Photo/Ctrl and867005 primary-light relay applications are logged. Exact tested source/DLL/log snapshot: `outputs/tested-photo-lighting/2026-10-06`.

This candidate adds the requested status card to the same Ctrl shortcut. It says **Detail override: ON** or **OFF** at the top centre, holds for900ms and fades over700ms. ON enables the existing geometry preference, captured entry fog and ordinary light-colour fade override; OFF uses native behaviour. The card is click-through and does not activate a window or take keyboard focus. It hides on Photo exit, focus loss or invalid/minimized target. The first valid Photo state4 entry or focused Ctrl toggle starts the independent message worker. Startup and loading states create no UI thread/window.

All camera, geometry, fog and light implementation files remain byte-identical to the tested lighting build. Only PhotoLOD notification integration and PhotoIndicator.h are added. GDI32 is the only added DLL dependency. Original full intro movies and INI stay installed.

`Build-StatusCandidate.ps1` runs the production native lighting relay across1920 cases and native unwind at all29 real instruction boundaries, plus fog/cache/texture-tail, lifecycle/startup/Ctrl/focus, movement/collision/geometry, native bitmap/DPI/GDI cleanup, hidden real UI worker/fade/restart and44 HID exports. Native ON/OFF previews: `work/native-abi/status-on.png` and `status-off.png`.

Runtime indicator visibility and startup remain pending. Exclusive-fullscreen composition may affect the separate native window. Lighting remains a partial improvement with unresolved additional limits; this UI addition does not alter those hooks.

Install with the game closed: `Install-StatusCandidate.ps1`. Guarded rollback to tested lightingfa3: `Restore-TestedLighting.ps1`. Confirmed fog2286 release remains separately preserved under `outputs/confirmed-photo-fog/2026-10-05`.
