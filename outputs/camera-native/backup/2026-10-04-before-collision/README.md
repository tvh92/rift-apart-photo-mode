# Automatic native Photo Mode boost

The Overstrike profile installs PhotoMode-10x-Tether1000.stage for the native Free camera's fixed 10x movement and 1000 tether. This separate, locally built hid.dll loads with the game and adds held-Shift 100x movement without starting the Python helper. Do not run the old helper at the same time.

Launch normally and choose Photo Mode > Free. Hold Shift while the game is focused to boost. Ctrl+Alt+F10 disables runtime boost until the next launch and restores the movement controller's captured baseline. Normal, Boost, and Tether can be edited in PhotoModeCamera.ini in the game folder; settings load at startup.

The DLL forwards all 44 exports of this machine's Windows HID library to the actual System32 DLL. Initialization starts on the first HID API call, outside DllMain. The worker verifies the exact RiftApart.exe SHA-256 before changing two virtual-method pointers. The hooks preserve the Windows x64 calling convention, and the module is pinned for the process lifetime. The Free-camera activation hook records its entity identity; the native movement-update hook checks that identity before adjusting the live controller on the game's update thread. No heap scan or external process is required. Other camera modes and gameplay movement are not intended targets.

This version supports only executable SHA-256 51299faca61866cf10ea9035a15b8f22600a56557dd5ffc1aad390d5a54e6d82. A different build leaves HID forwarding active and refuses camera hooks. Another loader using hid.dll conflicts; the installer refuses to overwrite an unknown DLL. Overstrike's script cleanup targets winmm.dll rather than hid.dll. PhotoModeCamera.log in the game folder records initialization, camera matching, and speed transitions.

The source is included here. It was built using the portable official Zig 0.15.2 compiler, with the archive checksum checked against ziglang.org's download index. No third-party camera DLL was downloaded. Isolated tests verified HID GUID forwarding, export resolution, unsupported-process refusal, hook ABI preservation, owner filtering, normal/boost/release values, baseline restoration, and replacement-camera identity. The user confirmed that automatic normal and Shift speeds work in-game and continue working after leaving and re-entering Photo Mode.

Close the game before running Install-NativeBoost.ps1 or Uninstall-NativeBoost.ps1. Removing this DLL disables automatic boost; disable the .stage mod and press Install mods in Overstrike to remove the fixed camera changes. The uninstaller preserves settings and logs. Saves are not edited by these tools.

Primary references: [Rivet's Rift Apart HID loader route](https://github.com/neptuwunium/rivet_hook), [Windows DLL search order](https://learn.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-search-order), [Windows x64 calling convention](https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention), [official Zig download index](https://ziglang.org/download/index.json).

Collision/no-clip and LOD remain unchanged.

