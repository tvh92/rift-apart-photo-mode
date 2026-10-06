# Rift Apart Photo Mode

Private development repository for the native Photo Mode extension and lighting/fog investigation for Ratchet & Clank: Rift Apart on Windows.

## Current result

User-confirmed camera movement is 10x, with held Shift selecting100x, a1000-unit tether, no-clip, and persistence after Photo Mode re-entry. Tapping Ctrl during Photo Mode toggles the detail override and shows a fading ON/OFF notice. The fog fix retains the processed entry fog settings; the user confirmed that distant pits recover their dark fog.

Lighting remains partially improved. The installed lighting-v2 build extends diffuse/specular fade handling, but the user reports no additional visible improvement from v2. Bridge lamps still disappear individually at a farther cutoff. Near/far/inside captures show a tentative pair dropping from the CPU submission list while four nearby candidates retain unchanged brightness. The exact selection gate is unresolved. Original full intro movies are restored; skipintro is abandoned.

Supported local executable SHA256:

```text
51299faca61866cf10ea9035a15b8f22600a56557dd5ffc1aad390d5a54e6d82
```

This is Steam build23987138. Hooks and installers must keep the full build guard.

## Where to continue

- [AGENTS.md](AGENTS.md): current implementation, authorization, exact hashes and research handoff.
- [Lighting/fog status](work/lighting-fog-current.md): confirmed observations and remaining work.
- [Next bridge diagnostic](work/bridge-light-next-diagnostic.md) and [request handle proof](work/bridge-light-query-handle-proof-main-luna.txt).
- [Current package](outputs/camera-native-lighting-v2): installed lighting-v2 source, audited DLL, build/install/rollback scripts and validation reports.
- [Confirmed fog snapshot](outputs/confirmed-photo-fog/2026-10-05), [tested lighting](outputs/tested-photo-lighting/2026-10-06), and [tested lighting-v2](outputs/tested-photo-lighting-v2/2026-10-06): preserved evidence and rollback sources.
- [Native probes](work/native-abi) and `work/test_*.py`: isolated verification tools. Many historical scripts are one-shot preparations; inspect before executing.
- [Archived research](archive/2026-10-04-completed): historical code and reports. Old status claims are superseded by AGENTS.md.

## Build and local dependencies

The current build entry is `outputs/camera-native-lighting-v2/Build-SpecularCandidate.ps1`. It expects verified Zig0.15.2 at `work/toolchain/zig-x86_64-windows-0.15.2/zig.exe` and invokes the native probes. Tool download provenance is retained in `work/toolchain/zig-download.json`. Python scripts require Windows and their documented packages; existing scripts use this machine's Python runtime path. Set those local paths deliberately when working on another machine.

Migration does not rebuild, install, change offsets, or change the game. Keep the game closed throughout any later installation, use guarded installers and rollback scripts, and finish audits before requesting a launch. Never modify saves or weaken unknown-build checks.

## Repository contents

Source, current and historical project documentation, generated research traces, comparison reports, screenshots, our own built proxy DLLs, and installer/audit manifests are versioned. Downloaded tools, compiler caches, game assets/movies/index backups, raw live memory captures and native probe executables remain local. [Local artifact manifest](migration/local-artifacts.json) records the excluded project's artifacts with sizes and SHA256 hashes; dependency directories are listed separately. A clone therefore needs those local dependencies/assets before historical reproduction or some audits can run.

The original local working files remain intact. Their existing layout is retained so relative build and rollback paths continue to work. Original absolute paths in historical evidence describe the original machine and are not portable setup instructions.
