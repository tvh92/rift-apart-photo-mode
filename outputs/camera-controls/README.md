# Installed Photo Mode camera

Current status and complete research handoff: ../../AGENTS.md.

`PhotoMode-10x-Tether1000.stage` replaces only the existing native Free camera's authored tether (1000), movement (20, 10x), rise (10, 10x), and acceleration (10000). The original base config is vanilla; the override is installed through Overstrike in d/mods/mod1. The locally built HID proxy DLL in ../camera-native adds held-Shift 100x movement automatically on launch. Both speeds, Photo Mode re-entry, and the combined two-second intro setup are user-confirmed working.

`Assert-CleanBaseline.ps1` checks the supported Steam build and pristine toc.BAK. `Check-Installation.py` audits both manager profiles/libraries, installed payloads, index sections, original base assets, and native DLL. `Reinstall-Camera.ps1` snapshots the current audited setup and installs that supported profile, with rollback on failure. Keep game and Overstrike closed throughout any reinstall. Do not reinstall after asking the user to launch a test.

The audit recognizes exact current payload hashes. A future camera change needs intentional audit/installer manifest updates; do not bypass checks by accepting arbitrary hashes. Never create a backup from a modded TOC or reuse old contaminated migration backups.

Normal/Boost/Tether settings are editable in the game's PhotoModeCamera.ini and load at startup. Ctrl+Alt+F10 disables runtime boost until next launch. Collision and LOD have not been modified; zero effect defaults are a new research target.

`presets`, `backup`, `change.json` and the original config under ../photo-mode-tether-1000 remain as reproducible asset inputs. `Set-CameraSpeed.ps1` is a historical direct-base-archive preset tool; active Stage overrides take precedence. Do not use it as the current mod installer.

Superseded Python helper/launchers, live logs and historical migration snapshots are in ../../archive/2026-10-04-completed/. They must not run alongside the installed DLL. The previous full README is preserved there as outputs/camera-controls/README.historical.md.

Primary sources: https://github.com/Tkachov/Overstrike/blob/OS/v1.8.1/Overstrike/Games/GameRCRA.cs and https://github.com/neptuwunium/rivet_hook.
