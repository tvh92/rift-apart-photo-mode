# Light query request worker traversal (0x12B8740)

Static, read-only disassembly of the RiftApart.exe build (same SHA as the earlier notes). All addresses are RVAs.
Labels: **[P]** means the disassembly proves it. **[H]** means it is a hypothesis.

## 1. Request arguments for LightSubmit (0x10BB680 -> 0x12B97E0 -> 0x107B750/0x107B760)

The 0x12B97E0 arguments, and the slot field each one lands in (via `request+N` copied to `slot+N+0x18` at 0x107B835..0x107B8A8):

| arg | 0x12B97E0 use | slot field | LightSubmit value (0x10BB745..0x10BB779, 0x10BB7F0..0x10BB833) |
|---|---|---|---|
| rcx | `manager = rcx + (sel+0x10E)*0x70` (0x12B9809..0x12B9824) | +0x38 | 0x6747580, sel=1 -> **0x674EC10** [P] |
| r9 | 0x100-byte shape, copied to a new buffer (0x12B986C..0x12B98E4) | +0x48 (ptr) | req1: view shape `rbp+30h` from 0x12BB640. req2: 0x1602E10 output (48.0 region) |
| arg5 | key value (low16) / key mask (high16) | +0x60 | **0**, so the entry-key test always passes [P] |
| arg6/arg7/arg8 | out array, capacity, count ptr | +0x68 / +0x64 / +0x70 | query+8 or +0x18, edi=`([0x674EC74]+16)&~15`, query+0x10 or +0x20 |
| arg9 | skip-prefilter flag | - | **0**, so the prefilter 0x1669FE0 runs at build time [P] |
| arg10 | visibility/occlusion context | +0x50 | **0 (null)** [P] |
| arg11 | optional 4x4 matrix (copied) | +0x58 | **0 (null)** [P] |
| (computed) | cell index list from 0x1669FE0, plus its count | +0x40 / +0x90 | u16 cell indices that survive the prefilter |

Note: on the request-build thread, 0x1669FE0 (0x12B9837..0x12B9866) already builds the list of candidate cells. The worker only visits those cells.

## 2. Manager 0x674EC10 data layout (as the worker uses it) [P]
- `mgr+0x00` = element-record base (r13). An output entry is `r13 + entryIdx*4`, which is a pointer to a record (0x12B8C1A..0x12B8C2A).
- `mgr+0x30` = cell array, stride 0x30. `mgr+0x48` = cell count-1 (0x1669FE4).
- `mgr+0x50` = block pool, stride 0x100. `mgr+0x60` = block count. `mgr+0x68` = optional per-cell sphere array, stride 0x10 (alternate prefilter).
- Cell (0x30 bytes):
  - +0x00 = AABB center xyz, +0x10 = half-extents xyz (0x12B8A00..0x12B8A31). The w lanes are forced to 0.
  - +0x20 = first block index, +0x24 = element count.
  - +0x2B bit 0x40 = cell enabled.
  - +0x2C = per-view occlusion cache bits.
- Block (0x100 bytes):
  - +0x00 = next block index (int; <0 or >= `mgr+0x60` ends the chain, 0x12B8BB0..0x12B8BC1).
  - +0x0A = int16 entry count.
  - Entries start at +0x10, stride 0x10: +0 u16 key, +4 u32 record index (in units of 4 bytes), +8..+0xF int16 x,y,z,r.
  - The x,y,z,r values are scaled by 0.5 (constant 0x32B4D70 = {0.5,0.5,0.5,0.5}), which gives a world-space bounding sphere.
- Record (the pointer that gets output): 3x4 transform at +0x00..+0x3F, local box center at +0x40, local box half-extents at +0x50 (read by 0x12B745E..0x12B74BA).

The structure is a **flat cell list (a spatial grid or bucket set), and each cell has a chain of fixed-size blocks**. There is no hierarchical tree: 0x1603D40 tests the cells one by one, in a single loop.

## 3. Traversal and tests, in order

### 3a. Cell prefilter (build time): 0x1669FE0 -> 0x1603D40 (or 0x1604B60) [P]
- 0x1669FEB: if `mgr+0x68 != 0`, it uses the per-cell sphere test 0x1604B60 (stride 0x10). Otherwise it uses the AABB test 0x1603D40 on `mgr+0x30` (stride 0x30).
- 0x1603DD0..0x1603F79 test each cell AABB against 16 planes stored SoA (4 groups x {nx,ny,nz,d}). For each plane the test is `c.n + d + |e|.|n| >= 0`, with abs via the mask at 0x2E6B300. If `minps` over all planes has any sign bit set, the cell is rejected (0x1603F58). Otherwise the u16 cell index is written out (0x1603F5F).

### 3b. Worker 0x12B8740 (one call per worker; cells are claimed with `lock xadd [slot+0x88]`)
- 0x12B8835/0x12B89A7: claims the next index and loops while it is `< slot+0x90`. The cell is `mgr+0x30 + idx*0x30` (0x12B89BF..0x12B89C7).
- **Gate A (cell enabled):** 0x12B89CB `test byte [cell+2Bh],40h`. If the bit is clear, the cell is skipped.
- **Gate B (cell non-empty):** 0x12B89D5 `cmp dword [cell+24h],0`.
- **Gate C (cell AABB vs shape again, 3-state):** 0x12B8A00..0x12B8A3D call 0x1603A80(&inside, &hit, shape, &cellAABB).
  - It writes `hit` at 0x1603CD1/0x1603CF5 and `inside` at 0x1603CF7.
  - If `hit==0` the cell is skipped (0x12B8A39).
- **Gate D (occlusion/visibility, skipped for lights):** 0x12B8A43..0x12B8B81. This runs only if `slot+0x50 != 0`.
  - It applies when the cell's cached bit `cell+0x2C & (1<<[ctx+14h])` is set, or when `(cellIdx&0xF)==(frame&0xF)`, `count>4` and the following distance check holds:
    `|ctx+0x60..0x68 - cellCenter|^2 > 16 * max(ext.x,ext.y,ext.z)^2` (0x12B8A75..0x12B8AC7, where 16.0 is the constant at 0x2E963A8).
  - In that case it calls 0x118CE60(ctx, ...) at 0x12B8B39. A false result sets the cache bit and **drops the whole cell** (0x12B8B68).
  - **LightSubmit passes ctx = 0, so this gate cannot fire for either light request [P].**
- **Element loop.** It walks the block chain. For each entry, `(key & slot+0x62) == slot+0x60` is tested at 0x12B8C10/0x12B8D30. The mask is 0 for lights.
  - **Cell fully inside** (`inside!=0`, no matrix, 0x12B8B9D..0x12B8C9F): every entry is appended with **no per-element geometric test**.
  - **Cell straddling** (0x12B8CA4..0x12B8F3B): the int16 sphere is tested against the 16 planes (0x12B8D3E..0x12B8E09).
    - If `min(dist)+r` has any negative lane, the entry is **rejected** (0x12B8E09).
    - If `min(dist)` is all non-negative, the entry is appended directly (0x12B8E22..0x12B8E2F).
    - Otherwise the entry goes to a "partial" list (0x12B8E34..0x12B8E3D). That list is refined by **0x12B72A0**, which transforms the record's local box (+0x40/+0x50) by the record matrix (+0x00..+0x3F) and tests it against the 16 planes. The record is kept if it is not outside (0x12B7810..0x12B781A).
  - The matrix path 0x12B8F40..0x12B91EC (with refinement 0x12B78B0) runs only when `slot+0x58 != 0`. It is not used for lights.
- **Append / commit sites (the element-append sites):** the local batch is at `rbp+2140h`. It is flushed when its size exceeds 0x3F0, and at the end of each cell:
  - 0x12B8C4F, 0x12B8E5B, 0x12B8ECB, 0x12B91FD, 0x12B927F: `lock xadd [r12=*slot+0x70],n`.
  - If the result is greater than `r15d=slot+0x64`, the count is clamped with `xchg` and the copy is truncated (0x12B8C58..0x12B8C6E).
  - The batch is then memcpy'd (0x2D27ABD) into `slot+0x68 + old*8`.
- Completion: `lock xadd [slot+8Ch]`. When the worker sees the final cell it calls 0x107A6E0 (0x12B9318..0x12B9339), which releases slot+0x20 and its dependents.

## 4. The request shape (16 planes) [P for structure, H for values]
- req1's shape comes from `0x1238E30(view, rbp+30h)` at 0x12BB7FB..0x12BB802.
- The perspective path, 0x12155C0 -> 0x1600E30(out, view+0x2E0, view+0x280), builds 6 frustum planes (0x1600E59..0x1600F12). It fills the remaining planes via 0x1600B90.
- The ortho path uses view+0x3F8..0x430 extents.
- 0x1234450 then optionally overwrites planes 11..15:
  - with a clip box, when `view+0xFE8` is set (center at view+0xFB8.., half-extents at view+0xFD0..0xFE4, 0x1234467..0x1234875);
  - and/or with `view+0x100C` user planes taken from view+0xFF4.. (0x123487D..0x12348E0).
- [H] One of the 6 frustum planes is the projection far plane. Its distance was not recovered statically.

## 5. Dispatch: 0x107AA50 [P, brief]
- It checks the predecessor `slot+0x10` and the dependency `slot+0x8` handles in the registry (0x107AA74..0x107AB5E).
- When it is ready and the work count `slot+0x90==0` (or flag `slot+0x84&2`), it marks done and calls 0x107A6E0 synchronously (0x107AB80..0x107AB90).
- Otherwise it pushes the slot handle into the ready array `registry+0x528/+0x534` (0x107ABA3..0x107ABC0) and signals the worker event at `registry+0x518` (0x107ABE5, 0x159C970).
- Requests that are not ready are queued on the pending lists 0x6414B60/0x6414B78.
- Worker/help loops invoke the callback through `call qword [slot+78h]` at 0x1079CE4, 0x1079E5D, 0x107A54D, 0x107BD1F and 0x107BDD5. That is 0x12B8740, run in parallel. Each invocation claims cells through `slot+0x88`.

## 6. Answers
1. **Structure:** a flat cell list (`mgr+0x30`, 0x30 B each), with chains of 0x100-B blocks (`mgr+0x50`) holding 16-B entries, and records at `mgr+0x00`.
   - Per-cell tests: the enabled bit `cell+0x2B&0x40`, `cell+0x24!=0`, and the cell AABB (`+0x00/+0x10`) vs the 16-plane shape, which is tested twice (0x1603D40 prefilter, 0x1603A80 classify).
   - Per-element tests: the key mask (no-op for lights), the int16 sphere (`entry+8..+0xF`, x0.5) vs the planes, and the record OBB (`rec+0x00..+0x5F`) vs the planes.
2. **Distance vs stored range:** the only distance comparison in the worker is gate D. It compares camera-to-cell-center squared distance against `16*maxHalfExtent^2` and then runs the 0x118CE60 occlusion test. **It is disabled for LightSubmit (slot+0x50 = 0).** No per-node or per-element max-view/LOD distance float is read anywhere in 0x12B8740, 0x1603A80, 0x1603D40 or 0x12B72A0. Every remaining test is plane-based against the request shape.
3. **Dispatch:** 0x107AA50 queues the slot for the worker pool, or completes it immediately. The callback runs on workers through `[slot+78h]`.

## 7. Best candidate for the per-group gate [H]
The **cell AABB (cell+0x00 center, +0x10 half-extents) vs the request planes**, checked at 0x1603D40 (build-time prefilter) and 0x1603A80 (worker), together with the **cell enable bit cell+0x2B&0x40** (0x12B89CB).
- A rejected cell removes all of its lamps at once, while lamps in neighbouring cells at the same distance survive.
- That matches the observed symptom if the bridge cell's stored AABB is stale or undersized, or if the cell is disabled or streamed.
- The distance dependence would then come from a far/extra plane in the shape (frustum far plane, the `view+0xFE8` clip box or `view+0x100C` extra planes) crossing the cell box, not the lamp spheres.
- Secondary candidate: the lamp record's OBB (`rec+0x40/+0x50` under the `rec+0x00` matrix) in refinement 0x12B72A0, if it differs from the light radius.

Runtime checks to discriminate:
- Locate the lamp's entry by scanning the block chains for the lamp record offset (`(rec - mgr[0])/4`) and note its cell.
- Compare that cell's +0x00/+0x10/+0x2B/+0x24 with neighbouring cells.
- Dump the 0x100-byte shape (`slot+0x48`) and evaluate each plane against the cell AABB at 150 and 170 units.
