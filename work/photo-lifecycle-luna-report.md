# Photo-mode lifecycle gate findings

Read-only static analysis of the supported local build. No game, installation, or source files were changed.

## Build and evidence

- `RiftApart.exe` SHA256: `51299faca61866cf10ea9035a15b8f22600a56557dd5ffc1aad390d5a54e6d82`.
- Evidence came from the existing PE/disassembly helpers and xref indexes under `work/`; no recursive compiler/cache scan was used.
- Addresses below are RVAs.

## Callback table and object argument

Main Photo-system vtable RVA `0x2FBF630` has slot 12 (`+0x60`) = `0x8DDA80`. Its bounds are `[0x8DDA80, 0x8DDB8B)`. The lazy initialization branch writes a static callback table at RVA `0x61381B0`:

- `0x8DDAC8–0x8DDAE0`: callback entry `+0x00` becomes `0x8DFD50`.
- `0x8DDAD8–0x8DDAED`: callback entry `+0x18` becomes `0x8DFA70`.
- Fast path at `0x8DDAA7` returns `&0x61381B0`; initialized path returns it at `0x8DDB7F`.

`0x8DFA70` bounds are `[0x8DFA70, 0x8DFD4A)`. It saves incoming `RCX` to `RBX` at `0x8DFA82` and consistently uses that same pointer for fields `+0x50`, `+0x54`, and for calls to enter/exit. It has no stack arguments in the observed code. The callback is therefore a one-object (`PhotoSystem* this`) callback; the object need not be recovered or cached from the Free camera.

`0x8DFD50` is the other table callback (`+0x00`), with bounds `[0x8DFD50, 0x8E0A80)`. It is a substantial per-frame system update. Its initial path checks setup byte `+0x54`; it has state-dependent work including a state-11 path and returns early for state 14 in some conditions. The exact ordering between callback entries `+0x00` and `+0x18` in the generic dispatcher was not recovered in this bounded pass.

## Setup and entry ordering

Entry routine `0x1A56D70` bounds are `[0x1A56D70, 0x1A56D93)` and has additional split code through `0x1A57203`. Its first checks at `0x1A56D79` and `0x1A56D86` require state `+0x50 == 0` and setup byte `+0x54 != 0`. It then dispatches main-system vtable slot `+0xC0` (`0x8DE720`) at `0x1A56DA0`.

Callback `0x8DFA70` calls `0x1A56D70` only on its state-0 path (`0x8DFAFF–0x8DFB0B`), then calls `0x8DE1D0` at `0x8DFB13`. The entry vfunc `0x8DE720` calls state setter `0x1A5AB40` at `0x8DECC5` with value 1. Setter bounds are `[0x1A5AB40, 0x1A5ABC0)`; it copies old state to `+0x4C` and writes new state to `+0x50` (`0x1A5AB47–0x1A5AB4A`). Thus the ordinary entry call changes state 0 to 1 before `0x1A56D70` returns and before callback `0x8DFA70` returns.

The setup byte is set at `+0x54` by helper `0x1A57370` (`mov byte [rcx+54h],1` at `0x1A57384`). Entry does not itself set that byte; it requires setup to have occurred already.

## State paths proven in the main callback

The observed ordinary entry sequence in `0x8DFA70` is:

1. State 0: call entry `0x1A56D70`; entry vfunc changes state to 1.
2. State 1: if `[this+0x870] == 0`, write state 4 and set `[this+0x89C]=1` at `0x8DFC26–0x8DFC2D`; otherwise write state 2 at `0x8DFB33` and issue an async event.
3. State 2: if `[this+0x89C] != 0`, write state 4 at `0x8DFC44`; otherwise remain at state 2.
4. State 4 is the steady state reached by these paths.

The callback also handles state 6 at `0x8DFC4D–0x8DFC61`: it calls `0x1A5CAA0`, then exit routine `0x1A57560`. Exit bounds are `[0x1A57560, 0x1A579E1)`. It stores 14 into `[this+0x50]` at `0x1A5758E`, before the virtual cleanup call at `0x1A57595` and the later restoration work. State 14 is therefore the closed/default state, and state 6 is already on the exit path.

The state-6 request is set inside `0x8DFA70`, at call site `0x8DFAE9` to setter `0x1A5AB40`; that callback returns via `0x8DFD35`. The state-6 branch that invokes Stop runs on a later callback. A prehelper that only checks the incoming callback state can therefore leave the gate enabled for the transition callback when it first sees state 4. To clear on the exact 4→6 transition, observe the setter call for this exact main-vtable object and clear when the new value is 6, or use a wrapper that calls the original callback and post-checks the state. Clearing on a later pre-state-6 callback is before Stop restoration but has one update of delay.

States 10 and 12 dispatch helpers `0x1A57210` and `0x1A579F0`; state 11 exits the callback early. Static evidence here does not establish whether every state from 1 through 13 denotes an active Photo camera. Avoid treating all nonzero/non-14 values as proven active. States `{1, 2, 4}` are the proven ordinary entry/steady path; state 6 must be disabled before chaining exit; 0 and 14 are closed/not-entered for this flow.

## Teardown

The main vtable slot 0 is `0x8DC3E0`, an allocator/deleting-destructor-shaped entry (it calls `0x8DC290`, then conditionally frees `0xC78` bytes). That path does not call lifecycle callback `0x8DFA70` or exit routine `0x1A57560`, so destruction is not guaranteed to pass through state 6. Vtable slot 2 is `0x8DD0C0`; it performs `0x1A57AF0` and `0x1A5C790` cleanup first, then writes 14 to `[this+0x50]` at `0x8DD0E8`.

If the runtime gate is a separately stored boolean, a prehook on the verified main vtable slot 0 can clear it before destruction. An exact-vtable check and a borrowed `this` pointer from the lifecycle callback keep the gate tied to the real shared Photo-system object rather than a cached camera owner. The callback table may be wrapped by preserving the pointer returned from `0x8DDA80` and interposing its `+0x18` entry after lazy initialization; concurrency and generic-dispatch ordering remain implementation details to validate separately.

## Gate recommendation and limits

For the observed ordinary flow, enable the geometry gate on callback states 1, 2, and 4; clear it on 0 and 14, clear immediately on the setter's exact-object transition to 6 if zero-frame close is required, and clear it in the main-object deleting-destructor prehook. A state-6 precheck alone clears before Stop restoration but one callback later than the 4→6 write. Do not extend the active-state allowlist to 3 or 5 or 7–13 from these findings alone; state 10/12 have active callbacks but their mode semantics were not proved here. Resolve those states from their setter callers or user runtime evidence if coverage beyond the ordinary 0→1→2/4 entry path is needed.
