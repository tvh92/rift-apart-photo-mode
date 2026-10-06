# Light query cull volume (`shape` at [rbp+30h] in 0x12BB640)

Static disassembly only (native_trace_full.py dumps). RVAs of the game EXE.

## 1. What `shape` is (PROVEN)

`shape` is a **16-plane convex volume**: a beveled view frustum, 0x100 bytes, planes packed SoA in 4 blocks of 4:

```
block b = i>>2 at shape + b*0x40;  lane l = i&3
  nx = +0x00+l*4,  ny = +0x10+l*4,  nz = +0x20+l*4,  d = +0x30+l*4
  index formula: ((i&0xC)<<2 | (i&3))*4  (0x1600D4F.., 0x12348A7..)
  plane: n.p + d, with d = -dot(n, point_on_plane)  (0x1600E0E xor -0.0, 0x12169CB)
```

Build path: 0x1238E30(view, shape) -> 0x12155C0(view, shape) then jmp 0x1234450(view, shape).

### 0x12155C0 (base volume)
- `view+0x438 bit 1 == 0` (perspective): tail-jmp **0x1600E30(shape, view+0x2E0, view+0x280)**.
  - Planes 0..5 = the 6 view frustum planes copied/transposed from `view+0x2E0..0x33F` (16 bytes each) (0x1600E53..0x1600F12).
  - Planes 6..15 = 10 edge-bevel planes from 0x1600B90(shape, idx, ptA, ptB, nA, nB): normal = cross(normalize(ptB-ptA), normalize(nA+nB)), d = -dot(n, ptA). ptA/ptB are frustum corners at `view+0x280 + 12*k`, nA/nB are pairs of the 6 face planes.
- `bit 1 == 1` (ortho): builds a local box descriptor on stack (rows view+0x00..0x28, half-extents 0.5*|+0x404-+0x400|, 0.5*|+0x40C-+0x408|, 0.5*(+0x430 - +0x3F8), plus +0x3E8/+0x3F0) and calls **0x16010A0** which writes the same 0x100-byte 16-plane layout (writes up to shape+0xFC, no calls). Constant 0x2E6A24C = 0.5.

### 0x1234450 (optional overrides)
- If `view+0xFE8 != 0`: overwrite planes 11, 12, 13, 14 with planes through camera position `view+0x30` and two corners of a box (centre `view+0xFB8..0xFC0`, half-extents `view+0xFD0..0xFD8` and `view+0xFDC..0xFE4`), via 0x1216850 (plane through 3 points). Plane 15 = normal `view+0xFC4..0xFCC`, d = -dot(n, view+0xFB8) (0x1234801..0x1234875). I.e. a portal/box-restricted pyramid with a cap plane. (Semantics of the box = hypothesis.)
- If `view+0x100C = N > 0`: copy N extra planes (stride 0x10, from `view+0xFEC`) into slots 16-N..15 (0x123487D..0x12348E0).

## 2. View fields feeding it and the far distance (PROVEN)

Frustum data is precomputed in **0x1212920** (view rebuild):
- 0x12121B0 (called at 0x1212DA4) builds the 8 world-space corners at `view+0x280..0x2DF` (12 bytes each):
  - corners 0..3 (0x280,0x28C,0x298,0x2A4) = pos(view+0x30) + R(view+0x00..0x28) * (unit corner dirs view+0x340..0x39C) * **near view+0x3F8** (0x12121BE, 0x1212225..).
  - corners 4..7 (0x2B0,0x2BC,0x2C8,0x2D4) = same with scale **view+0x430** (0x12125BE `movss xmm6,[rcx+430h]`).
  - Corner dirs at view+0x340.. come from projection extents view+0x3A0..0x3BC (from view+0x400..0x40C, +0x420..+0x42C) in 0x1212B6F..0x1212D99.
  - Ortho branch: 0x1214400(view+0x280, view, +0x400,+0x404,+0x408,+0x40C,+0x3F8,+0x3FC).
- 6 planes at view+0x2E0 + 0x10*k from corner triples via 0x10C7FA0 (0x1212DA9..0x1212E6A). Plane 0 (0x2E0: corners 0,2,3) is the near plane; plane 5 (0x330: corners 5,7,6, all far) is the **far plane**.

=> The far plane of `shape` is at distance **view+0x430** along view forward. view+0x434 is NOT read by the shape builders or 0x12121B0 (only stored).

## 3. Writers of near/far fields (PROVEN, from the dumps examined)

| RVA | writes | value |
|---|---|---|
| 0x1212F10 (projection setup, persp) | +0x3F8 / +0x3FC=+0x430=+0x434 | near = arg xmm1; far = min(arg xmm2, 32767.0 [0x32BA130]); then 0x1212920 |
| 0x1213240 (projection setup variant) | same four fields | far = min(arg xmm2, 32767.0) |
| 0x1214150 / 0x1214370 (set view/world matrix) | +0x430 = +0x434 = +0x3FC | reset to full far; tail-jmp 0x1212920 |
| 0x1212EA0(view, x) | +0x430 = max(g_0x67C1E54, min(+0x3FC, x)) only if that < current +0x430; +0x434 = x | then 0x1212920 |
| 0x12128F0 (leaf, caller 0x11D43E4 in 0x11D3500) | +0x430 like above, no +0x434 | jmp 0x1212920 |
| 0x1210080 (leaf, no floor) | +0x430 = min(+0x3FC, x) if smaller | jmp 0x1212920 |

The +0x430 shrink is one-directional (`comiss; jae skip`); it is reset upward only by 0x1214150/0x1214370 (or projection setup). g_0x67C1E54 is .data/BSS (0 at load), read-only references at 0x1212905 and 0x1212EC6; no RIP-relative writer and no pointer to it in .rdata/.data (probably a never-written floor = 0; hypothesis).

Other callers: 0x1234960 calls 0x1212EA0(view, view+0x3FC) at 0x1234A38 (no-op for +0x430 unless it is > +0x3FC; sets +0x434 = +0x3FC).

## 4. The frame function's second build (0x12BB97E..0x12BB9A5)

Condition: `obj = view+0x1BF0 != 0`, 0x1188FA0(obj, view, flags, 0) returns true, [0x6838420]==0, frame delta >= 2 (0x12BB8B2..0x12BB924). Then:
```
x = max( g_0x53393AC (0.0 static) + (64.0 [0x2F5B7EC] if 0x11F2950() && a slot at
         [view+0x1690]+0xCBE0/0xCFC0 is active, else 0),
         obj+0x174 + 1.0 )
0x1212EA0(view, x)  ->  +0x430 = max(g_0x67C1E54, min(+0x3FC, x)) if smaller
0x1238E30(view, shape)  -> rebuilds shape with the reduced far plane
```
So when this path runs, the light-gathering volume's far plane is pulled in to roughly `obj[0x174] + 1` (or +64 offset / global), capped by the projection far (+0x3FC, <= 32767). obj = view+0x1BF0 semantics unknown (hypothesis: a depth/occlusion or "max visible depth" provider; 0x174 looks like a measured distance). Because +0x430 is shrink-only and persists, the reduced far also affects anything else using view+0x280/0x2E0 until the next 0x1214150/0x1214370 reset.

## Open / hypotheses
- Identity of view+0x1BF0 object and meaning of +0x174 (dump 0x1188FA0 / 0x1188710 next).
- Which 10 of 12 frustum edges get bevel planes (not needed for the far question).

## 5. Far-plane reducers

### 5.1 obj = view+0x1BF0 is a software occlusion depth buffer, NOT the fog block (PROVEN)
0x1188FA0(obj, view, flags, 0) evidence:
- obj+0x18 = view+0x3FC (far) (0x11892B4..0x11892BD); obj+0x20 = max(2*near(+0x3F8), c); obj+0x24 = **32767.0 / far** (0x1189325..0x1189331); obj+0x1C/+0x28 from projection scales view+0x420/+0x424; obj+0x18C = camera pos delta (view+0x30 - other+0x30).
- obj+0x8/+0xC = integer width/height (imul, cvtsi2ss at 0x1189EEC..); job spawn via 0x107B4B0 with callback 0x118C130 (raster jobs, result in obj+0x440).
- **obj+0x170 is an int level index** (movsxd/loop counter at 0x1189A16, 0x1189E7E), not a float. obj+0x174 default = obj+0x18 = far (0x118993F..0x1189942); on success it is overwritten with **max(int16 samples of level [obj+0x170]) / obj+0x24** (0x1189E7E..0x1189ED7), i.e. the farthest depth (view units) found in the coarse occlusion depth buffer. Return value bl=1 on that success path, 0 if overflow (`[obj+0x5E0]` / `[obj+0x5DC]`, sets +0x184=0x101).
- The fog processed block lives inside the 0x760-byte job allocated by 0x11D3500 (r14 = 0x1209DA0(pool 0x6625040,0x760), processed block at r14+0x110; FB5EF0's +0x170/+0x174 are relative to that block, i.e. job+0x280/+0x284). Different object, different meaning; the +0x174 offset coincidence is unrelated.
=> Second-pass far in 0x12BB640 = max(g_53393AC [+64], **farthest occluder depth + 1.0**), clamped to <= view+0x3FC: an occlusion-derived far plane, not fog. Only applied when 0x1188FA0 returns true (depth buffer valid this frame) and other gates hold.

### 5.2 0x11D43E4 (call 0x12128F0 in 0x11D3500)
- r13 = view (arg rcx, reloaded from [rbp+580h] at 0x11D3F6E), r14 = job, rsi = selected atmosphere (r15 or rbx, 0x11D38AB).
- 0x11D3CB2..CCD: job+0x3B8 = view+0x3F8 (near), job+0x3BC = view+0x3FC (far); xmm13/xmm11 keep near/far.
- Branch: if atmosphere != 0 and atm+0x540 == near and atm+0x544 == far (0x11D422E..0x11D4244): if job near/far changed, it clamps (far = max(far, near + c)), runs 0x1213240 + 0x1214150 on a local view clone and copies 8 x 0x40 bytes back to the view (0x11D4348..0x11D43CC). Skips 0x12128F0.
- Otherwise (0x11D43D2): `x = job+0x3BC`; if x < view+0x3FC (xmm11) then 0x12128F0(view, x).
- No writer of job+0x3B8/0x3BC was found between 0x11D3CCD and 0x11D43D2 (direct code; 0x11D52F0, 0x11D5960, 0x11CB1A0 checked, they write elsewhere). So x == view far and the call looks like a no-op in practice. A write through an indirect call (0x11D52F0 has `call r8/r9`) is not excluded (hypothesis).

### 5.3 Is the reduced shape the one queried? (PROVEN for code order)
Order in 0x12BB640: 0x12BB802 shape#1 -> 0x12BB84A FB1130 -> **0x12BB881 0x11D3500** -> 0x12BB8F4 0x1188FA0 -> 0x12BB999 0x1212EA0 -> 0x12BB9A5 shape#2 -> ... -> 0x12BBD51 0x10BB680(rdx=&shape).
Calls in between: 0x1236850, 0x389950 x2, 0x1237C40, 0x135D7F0, 0x12139F0, 0x1239520, 0x105CD90, 0x10757C0, 0x10404C0. None gets [rbp+30h] (only lea at 0x12BBD4A), and none is 0x1238E30/0x1214150/0x1214370/0x1212F10/0x1213240. 0x12139F0 only writes jitter +0x428/+0x42C, view+0x40..0x7F and calls 0x1212920 (rebuilds view+0x280/0x2E0 from the existing +0x430, no reset); the stack shape is not touched.
=> When the second build runs, 0x10BB680 receives the occlusion-reduced shape. If it is skipped, shape#1 is used, built with whatever +0x430 is at frame start. Because +0x430 can only shrink, that is a value reduced in an earlier frame unless 0x1214150/0x1214370 reset it first (where that reset happens per frame is not traced here).
