# Native Photo Mode camera changes

Installed Overstrike asset mod: **10x default movement**, with **TetherDistance = 1000**. The original d/config archive is vanilla; Overstrike supplies the modified Photo Mode asset from d/mods/mod1. `NoIntro-Fixed-2Seconds.stage` is now enabled from d/mods/mod0 in both manager profiles. Legacy NoIntro is disabled. The original base movie archive is untouched. See ../startup-repair/NoIntro-Fixed-2Seconds.README.md for the successful two-second intro test and installation details.

## Baseline guard and audit

`Assert-CleanBaseline.ps1` refuses a missing, modified, or outdated `toc.BAK` and checks the current Steam build, depot manifest, and executable. `Check-Installation.py` audits either the camera-only profile or camera plus fixed intro, including payloads in both libraries, original base movie bytes, base config, and native DLL. The permanent combined setup passes this audit.

`Reinstall-Camera.ps1` provides a guarded reinstall of the currently supported profile: checks before and after installation, snapshots the current audited files, and restores those snapshots if installation fails. The old one-off `work/migrate_camera_overstrike.ps1` now routes to it; it cannot reuse its historical contaminated migration backups. Keep the game closed throughout installation.

These guards apply to our scripts. Overstrike's GUI is unchanged: it creates `toc.BAK` from the current `toc` when the backup is missing and otherwise reuses it. Never delete the backup while `toc` is modded. A game update needs a freshly Steam-verified baseline before reinstalling. The native HID camera DLL does not read or write either index file.

The file preset changes the Free camera's authored MoveSpeed from 2 to 20 and RiseSpeed from 1 to 10, with Acceleration 10000. The archive patch uses no injected code. An external runtime helper has now been added for in-game Shift boost, described below.

The 1000 tether was confirmed working in-game by you. You also confirmed that normal 10x movement and the held-Shift 100x boost work with the runtime helper. An automatic native DLL version is now installed; see ../camera-native/README.md. The user confirmed that both speeds work automatically and survive leaving and re-entering Photo Mode. Orbit, Selfie, light controls, collision, and LOD are unchanged.

## Restore or choose a temporary fixed-speed preset

These direct-archive presets are retained as research backups. The active Overstrike asset replacement takes priority over the base archive, so changing a base preset will not change the installed mod. Disable the camera mod and reinstall through Overstrike before using these legacy presets. Close the game first. Set-CameraSpeed.ps1 accepts `-Multiplier 1`, `10`, `100`, or `1000`; all retain the 1000 tether. `-Multiplier Vanilla` restores the original base configuration. The script checks hashes and refuses an unexpected base archive.

Example from this folder:

```powershell
.\Set-CameraSpeed.ps1 -Multiplier 10
```

These fixed presets load at startup. They are an interim test tool, not an in-game speed control.

## Overstrike package

PhotoMode-10x-Tether1000.stage packages the same verified Free camera asset as a Stage V2 mod. Its payload was decoded and compared with the original asset: only TetherDistance, MoveSpeed, RiseSpeed, and Acceleration change. The package preserves the original TOC header. It is enabled and installed through Overstrike; the installed asset matches the package exactly.

Migration restored the base config before installation, so disabling this mod and pressing Install mods in Overstrike restores original asset behavior. The automatic DLL must also be removed to restore all original movement behavior. Another mod replacing the same Photo Mode config asset can conflict; the last installed replacement wins. A game update or Steam verification may require reinstalling the asset mod.

This asset package does not include Shift boost. Overstrike 1.8.1's RCRA profile filters script packages and exposes no script settings, although its underlying ScriptsProxy source has an RCRA parser path. The automatic boost is implemented separately by the locally built HID proxy DLL in ../camera-native, so it does not rely on Overstrike's script settings or launch arguments.

Primary implementation references: [Rift Apart integration](https://github.com/Tkachov/Overstrike/blob/OS/v1.8.1/Overstrike/Games/GameRCRA.cs), [Stage installer](https://github.com/Tkachov/Overstrike/blob/OS/v1.8.1/Overstrike/Installers/StageInstaller.cs), [asset replacement](https://github.com/Tkachov/Overstrike/blob/OS/v1.8.1/Overstrike/Installers/InstallerBase.cs).

## Held Shift boost — runtime test

This Python helper is a fallback retained from research. Do not run it alongside the installed native DLL, since both change the same runtime movement fields. The native version loads automatically with the game.

CameraShiftBoost.py is an external process that reads and writes the existing native Free camera's configuration and the cached values in its matching movement controller. It injects no DLL or code. It checks the executable hash, process path, three native camera type pointers, and movement-controller ownership before writing. Native metadata, disassembly, and live memory confirm the field offsets.

Normal movement uses 10x speed; holding Shift while the game is focused uses 100x. Both use a 1000 tether. Camera and movement-controller values were read back independently, and you confirmed both speeds work in-game. Earlier tests failed because the movement controller caches configuration and because the game recreated the camera. The helper now searches the same allocation for a uniquely matching replacement camera and controller after recreation. While no valid pair is found, it waits without writing. This reattachment handling has not yet been tested through a complete leave-and-reenter sequence; if the helper stops, enter Free mode and start it again.

After launching the game and entering Photo Mode with camera type Free, double-click Start-CameraBoost.cmd to start the helper. It calls Start-CameraBoost.ps1. Stop-CameraBoost.ps1 requests a graceful stop. Ctrl+Alt+F10 also stops it. A normal stop restores the runtime values present before attachment, if the object still passes all checks. Closing the game discards these memory changes. The helper is limited to two hours per run and supports only this exact EXE build.

Custom speeds can be supplied as `-Normal 10 -Boost 100` to Start-CameraBoost.ps1. It identifies the camera automatically; it does not use the address from this research session on later launches. The Python runtime used is the existing bundled runtime on this machine; no Python package installation is required.

The four validated presets use the same serialized asset length and logical archive layout. For high-speed presets, acceleration is capped at 65535 to retain the original integer field width; horizontal and vertical speed multipliers are exact authored values. Runtime behavior may still impose other limits.

## Related installs

Overstrike 1.8.1 is installed in the sibling Overstrike folder. Both RCRA (Steam) profiles have legacy NoIntro disabled, fixed two-second intro enabled, the camera package enabled, and script support disabled. Original TOC backup: `toc.BAK` in the game folder, verified against Steam's current depot manifest. Both supplied download ZIPs were deleted after verification.

Overstrike uses the current working folder for Profiles and Mods Library. Start it from its own folder, rather than from an unrelated application's folder.

## In-game control research

The decoded UI config uses option IDs for FOV, vignette, exposure, and other controls. The reverse-engineered native option enum does not expose MoveSpeed, RiseSpeed, or a camera speed slider. This is evidence that adding a slider alone is insufficient, not proof that a runtime implementation is impossible.

The installed executable contains kCameraFast / FPS Cam Speed Up, but use by native Photo Mode is unconfirmed. CamCollisRad has a schema default of 0.2 and is a candidate collision experiment; radius zero has not been tested and is not an established no-clip switch.

Sources:

- [Photo Mode option IDs](https://github.com/neptuwunium/rivet/blob/a631c96ed6455f9873a646825d37883f99defa6e/Rivet.DDL.RCRA/Enums/x4f56b709.cs)
- [FreeMoveCamData](https://github.com/neptuwunium/rivet/blob/a631c96ed6455f9873a646825d37883f99defa6e/Rivet.DDL.RCRA/Types/FreeMoveCamData.cs)
- [Collision radius schema](https://github.com/neptuwunium/rivet/blob/a631c96ed6455f9873a646825d37883f99defa6e/Rivet.DDL.RCRA/Types/PhotomodeSystemConfig.cs)
- [Overstrike CLI implementation](https://github.com/Tkachov/Overstrike/blob/OS/v1.8.1/Overstrike/App.xaml.cs)

