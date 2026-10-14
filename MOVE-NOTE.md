# Move note (2026-10-14)

## Where it came from and where it is now

- Moved from `C:\Users\Tim\Documents\Codex\2026-10-04\prompt-for-the-research-instance-research`
- Now at `C:\Users\Tim\Documents\Bestanden\AI Projects\rift-apart-photo-mode`
- The whole folder was moved as-is, including `.git`, `archive/`, `outputs/` and `work/`. Nothing was deleted or rewritten.
- The small pointer folder `C:\Users\Tim\Documents\Codex\2026-10-04\rift-apart-photo-mode-continuation` is still there. Its `AGENTS.md` now points here.

## Git state

- Commit `61ada96` ("Install lighting-v3 far-cutoff candidate; update handoff") is already on `origin/main` (github.com/tvh92/rift-apart-photo-mode). Nothing was committed or pushed during the move, and there are no unpushed commits.
- The 18 uncommitted changes from the move came across unchanged. Since then, the 16 build and install scripts were edited (see the Python section below), so `git status` now lists 35 entries. None of it is committed yet. Decide whether to commit before continuing.
- `.git` is owned by the Windows account `CodexSandboxOffline`, not `Tim`. Git refuses to run in the folder by default ("dubious ownership"). Commands here were run with `git -c safe.directory=*`. To fix it permanently, either take ownership of `.git` or add a `safe.directory` entry to your global Git config. Not done yet.

## Workspace path updates

- `AGENTS.md` line 40 now names this folder as the workspace instead of the old Codex path.
- The pointer `AGENTS.md` in the Codex continuation folder now names the new location.
- `migration/local-artifacts.json` still lists the old `local_workspace` path. It is a historical record and was left alone.
- Historical backups and archived scripts under `outputs/camera-native/backup/` and `archive/` still contain old absolute paths. AGENTS.md says archived scripts are evidence, not active installers.

## Python for build and install scripts (done 2026-10-14)

- The 16 build and install scripts under `outputs/` no longer call the Codex-bundled Python (`C:\Users\Tim\.cache\codex-runtimes\...`). Each now resolves `.venv\Scripts\python.exe` relative to its own folder with `Join-Path $PSScriptRoot`.
- `.venv/` is a virtual environment in the project root, created from the system Python 3.14.2 (`C:\Users\Tim\AppData\Local\Programs\Python\Python314\python.exe`). It has no extra packages. The scripts use only the standard library.
- The Codex runtime used 3.12 and had extra packages. The build and install scripts do not import those packages. The research tools in `work/` that import `iced_x86` are not covered by this venv; install that package into `.venv` if you run them.
- The venv still uses the system Python 3.14 install, so keep that installation. `.venv/` is excluded from Git.
- Checked: the venv's stdlib imports work and the relative path resolves from each script folder. No build or install script was run, because that would touch the game folder.

## External, not inside this folder (expected)

- Game: `C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart` (Steam app 1895880, build 23987138)
- Dependencies, game assets and raw captures are excluded from Git and indexed in `migration/local-artifacts.json`. They stay local to this folder.
