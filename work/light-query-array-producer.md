# LightSubmitQuery `[q+8]` producer: why slot+0x68 != [q+8]

Static, read-only disassembly of RiftApart.exe (SHA256 `51299faca6...6d82`). All addresses are RVAs. No process, install or game file was touched.
**[P]** = proven by instructions. **[H]** = hypothesis.

## 1. 0x12B97E0: what reaches the slot's output field [P]
Frame = 5 pushes + `sub rsp,0A0h` = 0xC8, so stack arg5 is at `rsp+0F0h` and arg13 at `rsp+130h`. The request is built at `rsp+20h`, and 0x107B760 copies `req+N` to `slot+N+0x18` (0x107B835..0x107B8A8).

| request field | source | slot field |
|---|---|---|
| req+0x28 | r15 = u16 cell list (alloc 0x12B9843, `(cells+1)*2` B, filled by 0x1669FE0) | +0x40 |
| req+0x30 | r14 = 0x100-B copy of the r9 shape (alloc 0x12B9879) | +0x48 |
| req+0x38 | arg10 (`rsp+118h`), visibility ctx | +0x50 |
| req+0x40 | rdi = 0x40-B copy of the arg11 matrix (alloc 0x12B98FE, only if arg11 != 0) | +0x58 |
| req+0x48/+0x4C | arg5 (key) / arg7 (capacity) | +0x60/+0x64 |
| req+0x50 | **arg6 `rsp+0F8h`, the caller's array, stored unchanged** | **+0x68** |
| req+0x58 | arg8 = r12 count ptr (zeroed at 0x12B981D) | +0x70 |

- The three 0x10DBB30 allocations are only the cell list, the shape copy and the matrix copy. None of them is the output array.
- For request 1, 0x10BB76D passes `rcx=[q+8]` as arg6 and `q+0x10` as arg8. At registration, `slot+0x68 == [q+8]` exactly.
- (The earlier note's arg numbering is off by one, but its slot mapping is unchanged.)

## 2. Who replaces `[q+8]`: 0x10BB270 (post-gather filter setup) [P]
- Frame 0x12BB640 calls 0x10BB270(view, q) at 0x12BBE81.
  - This happens only when the query was freshly built by 0x10BB680 (`[rsp+50h]=1` at 0x12BBD63).
  - A reused query (`r13=[rsi+18h]`, 0x12BBD31..0x12BBD48, view+0x11DA) skips both the build and this step.
- 0x10BB29A..0x10BB2A7 waits (0x107BAE0) for **both** gathers, handles `q+0x68` and `q+0x70`.
- 0x10BB2CF..0x10BB2FC:
  - allocates a **new** array of `([q+0x20]+[q+0x10])*8` bytes (0x10DBAE0, tag 0x32D4CC0);
  - saves `r15=old [q+8]` and `rdi=old count`;
  - then **writes `[q+8]=new` and `[q+0x10]=0`**.
- So after this point, request 1's `slot+0x68` still points at the raw gather (old array), while `[q+8]` is a different buffer.
  - `*slot+0x70` (= q+0x10) is the new filtered count, so it is the wrong count for the old array.
- Mode branch on global byte 0x533953F:
  - **== 0 (normal; live counts >20 confirm this)**: 0x10BB5BA..0x10BB64F schedules job **0x10B9A50** through 0x107B4B0 with work count = old count. The parameter block lands in the job slot at +0x30 (old array), +0x38 (q), +0x40 (vis ctx), +0x48 (view). The job handle is written to **`q+0x78`**.
  - **!= 0 (alternate mode)**: if the count is <=20, the entries are memcpy'd. Otherwise each light is kept when `|rec+0x30 - view+0x30|^2 < 22500.0` (0x32D4EB4, i.e. 150^2) (0x10BB3B0..0x10BB538), sorted, truncated to 20 (0x10BB573), and copied into new `[q+8]`. In this mode 0x11EE3A0 also suppresses request 2. [P] code / [H] that it is inactive in the user's runs (inferred from the 91..143 submitted counts).
- 0x10BA710 starts with `wait [q+0x78]` (0x10BA738..0x10BA752), so ranking consumes only the job's output.
- 0x10B9A50 is referenced only from 0x10BB643. 0x10BB270 is called only from 0x12BBE81.

## 3. Job 0x10B9A50: per-light pre-upload filter (raw gather -> `[q+8]`) [P]
- It claims 16-element batches via `lock xadd [slot+88h]`.
- Kept records are batched on the stack, then appended to `[q+8]` with `lock xadd [q+10h]` + memcpy (0x10B9CC3..0x10B9CE7).
- Order is not preserved across workers.
- For each record `rec` (the gathered light source):
  1. 0x10B9B90: `f = [rec+88h] & 0x1FFFFFFF` is written back. This clears per-frame mark bits 29..31, which 0x10BA710 sets at 0x10BAC8A/0x10BACB9.
  2. 0x10B9BAB: drop if `f` bit 2 (0x4) is clear.
  3. 0x10B9BB6: if byte 0x67478B4 is set, keep only `rec == 0x12B6810(0x67478B0)`. This is a handle lookup into the 0x6747CE0 table. [H] It is a debug "isolate one light" mode.
  4. 0x10B9BC6: if byte 0x53394EC == 0, drop if `f` bit 4 (0x10) is set.
  5. **0x10B9BDD..0x10B9C07, far cutoff:** if `f & 0x40000` (bit 18):
     - `d = 0x10B9750(rec, view+0x30)`;
     - **drop if `d > [rec+0xA0]`**.
     - 0x10B9750 = max(0, |M(rec+0x40) - cam| - max(rec+0x70,+0x74,+0x78)*rec+0x4C). That is the front-of-bounds distance, the same formula used by RGB fade 0x1098F90/0x1099200.
  6. **0x10B9C0D..0x10B9C3F, near fade:** if `f & 0x80000` (bit 19):
     - `t = clamp(|rec+0x30 - cam| * [rec+9C] + [rec+98], 0, 1)` (0x389950 is Euclidean distance);
     - drop if `t <= 0`.
  7. 0x10B9C41..0x10B9C70, colour/type: with `s = [rec+A8]+[rec+AC]+[rec+B0]`:
     - if `s > 0`, drop when type byte `[rec+94h] == 5`;
     - if `s <= 0`, drop unless type == 4.
  8. 0x10B9C72..0x10B9C89, occlusion:
     - applies if the ctx is non-null. Ctx = `view+0x1BF0` when `view+0x11D8 != 0` and `[ctx+184h]==0` (0x10BB2AE..0x10BB2CA);
     - calls `0x118CDC0(ctx, rec, 0.01)`, which transforms the rec OBB (+0x40/+0x50 under the +0x00 matrix) and calls the same occlusion test 0x118CE60 used by worker gate D;
     - false -> drop, counted into global **0x5324830** (`lock xadd` at 0x10B9D48).
- Completion: `lock xadd [slot+8Ch]` -> 0x107A6E0.

## 4. Later writers of `[q+8]` (0x10BA710) [P]
- 0x10BA95D..0x10BA99B: sorts `[q+8]` in place (0x159A2F0, comparator 0x10B9550). Membership is unchanged.
- 0x10BAB10..0x10BAC69: ranks the request-2 list `[q+0x18]`:
  - by squared distance from `view+0x30`;
  - invalid when `[rec+88h]&0x1810010`, or bit 2 is clear, or `([rec+8Ch]&mask)==0`.
  - The survivors are compacted into a new buffer, and **`q+0x18`/`q+0x20` are replaced** (0x10BAC65/0x10BAC69).
- 0x10BAC78..0x10BACE2: appends each secondary to `[q+8]` unless it is already present:
  - sets rec+0x88 bits 29/30;
  - `[q+8][q+0x10]++`;
  - hard cap 0x200.
  - **Secondaries do not pass through the step-5/6 distance drops.**
- No other write to `q+8` was found in 0x10BB680, 0x12BB640 (between 0x12BBD51 and 0x12BC169), 0x107A6E0 or 0x10BA710.
  - 0x107A6E0 only releases `slot+0x20` and walks the `slot+0x10` successor chain. It runs no copy callbacks.

## 5. Interpretation
- [P] `[q+8]` = filter_0x10B9A50(raw gather at request1 slot+0x68) ∪ secondary merge.
  - The "only 64/192 shared" result is expected: the two arrays are different buffers.
  - The observer also indexed the old array with the new count.
- [P] The installed lighting-v2 relays clear bit 18 only inside the RGB fade writers (0x1099200/0x1098F90).
  - The same bit-18 test in 0x10B9A50 step 5 runs earlier and **removes the light from `[q+8]` entirely** once its front-of-bounds distance exceeds `rec+0xA0`.
  - This explains why v2 produced no visible improvement.
- [H] Steps 5 and 8 are the prime candidates for the bridge z~42 pair:
  - step 5 if the pair has bit 18 and `rec+0xA0` falls within the 137..166 centre-distance bracket, minus the bounds radius;
  - step 8 if the occlusion ctx is active in Photo view.
  - Step 6 is a near-fade (drop when *too close*/fade<=0 per coefficients) and is less likely.

## 6. Next checks (read-only, live)
1. Find the job slot by `q+0x78` (same key format as 0x107BAE0). Verify:
   - callback `slot+0x78 == 0x10B9A50`;
   - `slot+0x38 == q`;
   - `slot+0x30 ==` request1 `slot+0x68`;
   - `slot+0x90` = old count.
   Then diff the arrays using their correct counts.
2. For each dropped light, log:
   - `[rec+88h]` bits 2/4/18/19;
   - `[rec+A0h]`, `+98/+9C`, `+70..+78`, `+4C`, `+94`, `+A8..+B0`;
   - the 0x10B9750 distance;
   - the delta of 0x5324830 per frame.
3. [H] Candidate Photo-only patch (not built, not installed): skip the step-5 `ja`.
   - Location: 0x10B9C07 (`0F 87 8C 00 00 00`).
   - Context bytes 0x10B9BE6..: `41 8B C0 C1 E8 12 A8 01 48 8B 44 24 38 74 18 48 8B D0 48 8B CB E8 50 FB FF FF 0F 2F 83 A0 00 00 00`.
   - The job runs on worker threads, so it needs a view/Photo-gated relay (`[rsp+38h]-0x30` = view), not a global byte flip.
