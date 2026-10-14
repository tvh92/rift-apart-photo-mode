# Light query reuse and Ctrl response (read-only, exact build)

Build: RiftApart.exe SHA256 `51299faca6...6d82`. Static source/disassembly review plus already-preserved observer snapshots only. No live process access or code/install changes.

## Reuse predicate in `0x12BB640`

The branch at `0x12BBD20..0x12BBD51` requires all of:

1. incoming `r15d` bit 1 set (`test r15d,2`);
2. saved second argument (`rsi`, original `RDX`) non-null;
3. `[rsi+0x18]` non-null, which becomes the query pointer;
4. `[view+0x11DA]` nonzero.

If any fails, it calls `0x10BB680(view, &shape)` to build/retrieve a query. When reuse succeeds, it sets the local “fresh” byte to 0 and skips that call. The branch does not compare frame number, camera transform, Ctrl state, or query generation.

`view+0x11DA` has one direct `.text` initialization store found by scanning its disp32 references: `0x1236135: mov word [rbp+0x11DA],1`; the other references in `.text` are the three reads in `0x12BB640`. This supports it as an initialized reuse opt-in, but does not identify its higher-level name/semantics.

## Known exact-build callers rule reuse out

The preserved xref list (`light-frame-job-return-refs-main.txt`) contains three direct callers of `0x12BB640`:

- `0x108B571` passes `RDX=0` (`xor edx,edx` immediately before the call), so the cache argument is null.
- `0x10DF884` also passes `RDX=0`.
- `0x1204AF7` passes `RDX=RBX`, but its caller first zeroes the stack record at `RBX`, including `[RBX+0x18]` (`movups [rbp+0x10],xmm0` clears bytes `+0x10..+0x1F`). Thus the query pointer tested by the reuse branch is null.

Therefore the reuse predicate is false for all three known call sites. With exhaustive direct call references in the retained index, the evidence strongly establishes that these native frame paths call the query builder each time. `0x10BB680` allocates/initializes its query record and clears its payload before registrations; a stable query address in observer snapshots can result from allocator reuse and does not show the `0x12BBD31` cached-query branch was taken.

The low-level flag source is caller-specific (`r13d`, `ebx`, or `edi` at the three call sites); its semantic name is not established. In this path, however, it cannot enable query reuse because the cache argument/pointer prerequisites fail independently.

## Ctrl relationship and stale-query conclusion

No reuse predicate input is the mod's Ctrl state. The native `0x12BB640` caller and `0x10BB680` builder contain no reference to the plugin gate. The plugin changes its shared comparison flag from the Photo tick; the worker `0x10B9A50` reads that gate at its distance branch. Since query filtering runs asynchronously and ranking waits on its job handle (`q+0x78`), an input edge could theoretically occur while a just-built request is in flight. Static evidence does not establish whether that produces a visible frame of mixed comparison state or poor response.

The stale-cache explanation from the prior review should be withdrawn for these three known native call paths: their branch conditions force a fresh query build, independent of Ctrl. The cached branch remains an exact native behavior for some possible caller state, but no direct call site reviewed here can reach it and no corresponding Ctrl transition/invalidation behavior is demonstrated. Existing captures of stable query addresses across samples cannot identify the branch; they also show query counts and membership change between positions, consistent with rebuilt contents.

## Diagnostic/design conclusion

No stale-query bypass/invalidation hook is justified. No cache-specific code change is indicated for the known call paths. The narrowest useful toggle diagnostic is to correlate, for one nearby light and adjacent frames, Photo-tick Ctrl state/edge time, the `0x12BB640` fresh-vs-reuse local byte, query contents after `0x10BB680`, the filter job's gate value at `0x10B9C07`, and the submitted list. Use a bounded per-frame record and keep the combined Ctrl behavior unchanged. This would test a possible one-job timing race and independently expose the nearby-light rejection stage.

## References

- `work/light-view-query-owner-main.txt`: `0x12BB640` reuse/build branch and `0x10BB680` query initialization.
- `work/light-frame-job-return-refs-main.txt`: complete direct-call xref list for `0x12BB640`.
- `work/light-query-array-producer.md`: fresh query filtering, job completion, and array distinctions.
- `work/live-lights-readonly/20261006T003720556776Z-bridge-all-lit-ctrl-on-3.json`, `...004052639268Z-bridge-pair-dark-ctrl-on-1.json`: same view/query addresses with changed array counts across camera positions; address identity alone is not a reuse-branch marker.
