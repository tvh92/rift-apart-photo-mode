# Revised Ctrl/indicator candidate — 5 October 2026

Installed DLL SHA256: `7d4234168e04020b65bd2af2a88314bffe9bef2baadeb2994c2901b539008665`.

The user confirmed that rolling back the eager-indicator build06ce to previous geometry build7508 fixes startup in their test. The exact hang mechanism remains unproven. Failed code/logs are retained, including `backup/2026-10-05-failed-eager-indicator/` and `work/control-indicator-loading-failure-2026-10-05.log`. The successful rollback log is `work/control-indicator-rollback-working-2026-10-05.log` and also shows many active Photo geometry toggles.

This revision removes the UI start from native initialization. Only a state4 Photo notice, with ready/setup/enabled checks and visible focused same-process target, may start the worker. Show/Hide/F10 requests only update queued state. The once-start CAS guard is reset on registration/window failures or completed worker exit, allowing later Photo entry/toggle to restart after owner-window destruction. The foreground validation also rejects a NULL window explicitly. The worker still runs separately and never waits for the game callback.

Ctrl tap/release, modifier/focus cancellation, the900ms hold plus700ms fade, and the existing geometry/camera/collision implementations are preserved. No geometry patch bytes, native selectors or assembly changed. Lighting/fog remain unpatched. Texture/streaming/native resource floors remain unchanged.

Tests passed: startup states14/10/11/0/1/2 create zero UI threads; active Photo creates one; duplicate starts rejected; notifications alone never start UI; real worker messages/timer/fade/cleanup/restart; lifecycle/Ctrl/chord/focus tests; normal/Shift/baseline/no-clip/disable behavior;96/144/192DPI card/alpha/GDI cleanup; HID proxy exports and unsupported-process refusal. Independent read-only review found no blocker. Results: `work/lazy-indicator-validation.json` and `outputs/camera-native/proxy-test.json`. Source hash/rollback/INI checks pass.

Installation audit `outputs/camera-native/lazy-indicator-installation-audit.json` verifies new DLL, exact EXE, unchanged INI, same four asset overrides, matching Overstrike profiles/libraries, pristine TOC backup, vanilla base config and original movie bytes. No asset, intro, settings, save or profile edits. Verified7508 rollback remains available through `Restore-PreviousLODDLL.ps1` with the game closed.

Runtime confirmation still needed: launch normally and first check loading reaches the game. Then enter Photo Mode, tap Ctrl twice and check ON/OFF/fade. Exit/re-enter to check a new notice. Do not change installed files after requesting that test. Fullscreen composition can still affect visibility. If a display-mode change recreates the main HWND while Photo state and preference remain unchanged, the next toggle or Photo re-entry restarts the indicator.
