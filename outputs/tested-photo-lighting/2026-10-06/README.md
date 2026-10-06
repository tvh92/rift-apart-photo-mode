# Photo Mode lighting candidate

This separate candidate preserves the user-confirmed fog release2286. Ctrl controls geometry, entry fog and the ordinary light colour fade override. No indicator. Original full intro movies stay installed.

The native ordinary-light helper applies a fade based on the camera's distance before copying RGB into the128-byte g_Lights shader buffer. The candidate clears just that far-colour-fade bit in the helper's register copy. It never changes source lights or their attenuation radii. Native near fade, the separate specular scalar, light type, debug scaling and camera position stay intact.

One exact eight-byte MOVSD at RVA1099270 is replaced atomically with a jump to a registered leaf relay. It only acts when the existing Photo Ctrl preference is active, the caller is one of four verified ordinary-light submissions, and R14 is the native primary view. Other views, callers and gameplay retain native flags. The relay replays MOVSD and uses native chained unwind metadata without allocating a frame. A process-lifetime counter is logged at Photo teardown for verification.

Build and isolated tests: `Build-LightingCandidate.ps1`; manifest: `build-verification.json`. Tests execute the exact637-byte helper and real production relay across1920 cases, plus native unwind at every relay byte, source immutability, off/ready/view/caller filters and atomic restoration. Fog, lifecycle, Ctrl, camera, no-clip and HID forwarding regressions also pass.

Runtime lighting result is pending. This targets ordinary light types0..3; type4's specular fade, ranking/capacity, streaming, shadow policy and source light radius remain native. The shader bridge proves where this fade goes, but the Corson V comparison is needed to establish whether it solves the reported disappearing illumination.

Install only with the game closed using `Install-LightingCandidate.ps1`. Roll back to the exact user-confirmed fog DLL using `Restore-ConfirmedFog.ps1`. Confirmed source/DLL snapshot: `outputs/confirmed-photo-fog/2026-10-05`. No save changes.
