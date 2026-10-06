# Control/indicator review — 5 October 2026

Installed candidate: `06ce078afaca25aeb95cca6da595ea8f8b54f8a9ccac3aef833c64fadb6a6de8`.

The independent read-only review found no blocker for focused Ctrl tap/release or normal Photo Mode exit/re-entry. Indicator request mode and target are captured under one SRW lock, a serial rejects superseded requests, and the UI worker owns its HWND/GDI operations. The module stays pinned for process lifetime. Native styles and show flags prevent activation; cleanup hides the window and releases drawing resources.

One UI limitation remains: if the game destroys and recreates its main HWND without exiting, Windows destroys its owned indicator window and the worker exits. The indicator starts once, so later notices would require restarting the game. This does not disable the Ctrl toggle or geometry gate. Actual exclusive-fullscreen visibility also needs in-game verification. Neither issue was observed in a running game during this turn.

Isolated probe results: `work/control-indicator-validation.json`. Installed file checks: `outputs/camera-native/controls-indicator-installation-audit.json`. Runtime Ctrl/indicator confirmation remains pending. Lighting and white pit fog are not patched.
