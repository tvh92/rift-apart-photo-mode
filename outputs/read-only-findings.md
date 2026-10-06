Historical discovery report: current installed and user-confirmed camera status is documented in ../AGENTS.md. Statements below that tether or runtime behavior are untested describe an earlier stage.

# Rift Apart Photo Mode: read-only findings

Inspected on 4 October 2026. No game files or saves were changed. The game was not launched, attached to, or memory-patched. No third-party binaries were downloaded or run.

## Installed build

- Installation: `C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart`
- Steam app: 1895880
- Installed Steam build ID: 23987138 (from the local app manifest; not an assertion that this is the newest available build).
- RiftApart.exe SHA-256: `51299FACA61866CF10EA9035A15B8F22600A56557DD5FFC1AAD390D5A54E6D82`
- `toc` uses outer magic `34E89035` and a DAT1 container.
- `d/config` uses DSAR version `00010003`, compression type 3 (LZ4).

## Photo Mode tuning actually present in this build

Read-only DSAR decompression and DAT1 serialized-field parsing identified a `PhotomodeSystemConfig`. Its archive position was cross-checked against the TOC metadata and asset ID.

- Asset ID: `AED6101948AAFA54`
- Archive: `d/config`
- Decompressed archive offset: 10830144
- DAT1 asset size: 263280 bytes
- TOC asset index: 65761 (zero based)
- TOC separate header offset: 2351412

Selected authored values:

| Field | Value |
|---|---:|
| Camera named `Free`: `CameraType.Obj.CamData.TetherDistance` | 10 |
| Camera named `Light Mode`: `CameraType.Obj.CamData.TetherDistance` | 15 |
| Root `FreeMove.TetherDistance` | 10 |
| `LightSettings.Orbit.MaxDistance` | 8 |
| `LightSettings.Orbit.MinHeight` | -7 |
| `LightSettings.Orbit.MaxHeight` | 7 |

The Free camera uses `PhotomodeCameraFreeMovePrius`. Light Mode uses the same type and has the description "A fancy camera, just for light mode". These are authored data values in engine units, not measured camera ranges or a calibrated distance in metres. Camera tether values and light placement limits are distinct controls.

`UIPhotoModeConfig` was also found (asset ID `8E1F557CB712559F`). A `PerfSpecConfig` contained PS5-labelled performance specifications; that does not establish which specifications govern PC rendering.

## Reproducible public references

- [ALERT DSAR codec](https://github.com/Tkachov/ALERT/blob/bc90ed9b53fbcaa3b7acf94b36f00e77eab0dacb/dsar_codec.py)
- [ALERT DAT1 reader](https://github.com/Tkachov/ALERT/blob/bc90ed9b53fbcaa3b7acf94b36f00e77eab0dacb/dat1lib/types/dat1.py)
- [ALERT serialized-field reader](https://github.com/Tkachov/ALERT/blob/bc90ed9b53fbcaa3b7acf94b36f00e77eab0dacb/dat1lib/types/sections/__init__.py)
- [ALERT TOC asset metadata](https://github.com/Tkachov/ALERT/blob/bc90ed9b53fbcaa3b7acf94b36f00e77eab0dacb/dat1lib/types/sections/toc/sizes.py)
- [Rivet FreeMoveCamData schema](https://github.com/neptuwunium/rivet/blob/a631c96ed6455f9873a646825d37883f99defa6e/Rivet.DDL.RCRA/Types/FreeMoveCamData.cs)
- [Rivet PhotomodeSystemConfig schema](https://github.com/neptuwunium/rivet/blob/a631c96ed6455f9873a646825d37883f99defa6e/Rivet.DDL.RCRA/Types/PhotomodeSystemConfig.cs)
- [Overstrike file-based stage installer](https://github.com/Tkachov/Overstrike/blob/9f906ca09ea5ce4b84528410171c235bc4b0bfe6/Overstrike/Installers/StageInstaller.cs)
- [rivet_hook runtime camera implementation](https://github.com/neptuwunium/rivet_hook/blob/dab6cc6b42f4dcad96dac0757281d82bc40c94d8/src/camera.cpp)

## What remains unvalidated

No runtime behavior was tested. In particular, the engine might clamp, copy, ignore, or supersede one of the authored tether values. Collision, level streaming, far clipping and world completeness have not been measured. No file-only global LOD override has been demonstrated here.

Minimum next validation: in a separate reversible test installation and disposable save, replace only the Free camera's authored tether value with a finite 1000 using a correctly packaged asset override, enter the existing Photo Mode, and measure whether movement passes the vanilla limit. Keep all LOD data unchanged for this first test. If ineffective, test the separate root `FreeMove.TetherDistance` field independently before concluding that a runtime hook is necessary. This test has not been performed.

## Subsequent user-authorized installation

Later on 4 October 2026, the user requested actual installation for testing. The native Free camera's `TetherDistance` was changed from 10 to 1000 in `d/config`. The serialized numeric type was widened from uint8 to uint16 within its existing padded field space. The modified DSAR archive was validated before installation and decoded again after installation. Only three decompressed bytes changed. No DLL, executable, TOC, LOD field, Light Mode camera tether, root FreeMove tether or save was changed. Runtime behavior remains untested.

The original archive, hash manifest and `restore.ps1` are saved under `outputs/photo-mode-tether-1000/`. Close the game before restoring. The restoration script verifies both hashes and refuses to overwrite an unexpected archive changed by a later update or mod.

