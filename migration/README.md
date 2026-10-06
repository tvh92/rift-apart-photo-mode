# GitHub migration

Repository: [tvh92/rift-apart-photo-mode](https://github.com/tvh92/rift-apart-photo-mode), private, default branch `main`.

The existing project directory was initialized as the local Git working copy on6 October2026. No game files, native code, saves, assets or installed settings were changed by migration. The directory layout is retained for source/build/rollback references.

`local-artifacts.json` lists excluded local project artifacts with size/SHA256, plus separate dependency/cache directories. Game archive/index/movie/config binaries and raw process captures are not uploaded. Downloaded Zig, iced_x86 and Overstrike runtimes stay local; toolchain provenance is tracked. Our own proxy DLLs and their exact rollback sources/audits are included.

`pre-push-audit.json` records scope, file counts, own DLL hashes and the high-confidence credential scan. `remote-verification.json` is generated locally after pushing and is intentionally excluded from Git to avoid self-referential commit metadata.

The previous, stale continuation prompt is preserved as `CONTINUE-PHOTO-MODE.before-git.md`. The root continuation prompt now reflects confirmed no-clip/fog/notice results, abandoned skipintro, and unresolved illumination. Read root AGENTS.md before consulting historical reports.
