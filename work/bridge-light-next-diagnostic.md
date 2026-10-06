# Bridge lighting: next diagnostic boundary

The completed Ctrl-ON comparison is retained in `bridge-light-cutoff-bracket.json`. Two of a tentative six-light bridge group drop out of the CPU pass67 submission list beyond the observed cutoff; the four retained members have unchanged RGB. This does not yet identify source objects or the rejection branch.

Do not extend another fade distance or bypass every source eligibility test on this evidence. Current installed lighting-v2 remains the user-tested baseline, including Ctrl, the confirmed fog behavior and fading notice.

The external observer finds primary-owned query candidates through typed request callbacks, but their request output pointers differ from the current query arrays. It refuses source-array reads. Resolve query lifetime/copying first; the current candidate address is not sufficient proof.

Offline follow-up found a stronger ownership link: `10BB786` stores the fixed request token at query+70 and `10BB83D` stores the optional token at query+68. `107B760` builds that same token from registry generation, slot index and registry bit, stores it in slot+0 and returns it. See `bridge-light-query-handle-proof-main-luna.txt`. The existing metadata stops at query+28, so it cannot retrospectively validate those fields. A future bounded observer can match the exact token plus callback, manager, derived count pointer and primary view, then label request output and current ranking arrays separately. Optional replacement is proven at10BAC65/69; fixed pointer mismatch remains unexplained. Implement and isolate-test this guard before another live capture; do not simply drop array equality from the current observer.

If external ownership cannot be proven, the next concrete diagnostic candidate should observe the primary frame call at RVA12BC169 to original10BA710 and the following12BC17C to10B9DB0. The former performs ranking/selection; the latter builds LightSubmit records. A bounded copy of query/source identity before and after selection, after native request completion, could separate query rejection from later record rejection. This is a proposed logging boundary only, not a hook whose ABI/unwind/lifetime safety has been established. No installation or runtime change is authorized by this document alone; existing user authorization remains scoped to guarded Photo Mode work.

Before any new candidate installation: prove exact call bytes, request completion order, arguments and unwind behavior; impose primary-view/Photo/EXE guards and capped storage; preserve source fields and native execution exactly once; build and run meaningful isolated ABI/ownership/limit checks; finish installation/audits with the game closed before requesting another launch. Keep original movies and all current camera/fog controls.

The current captures performed no process writes. User was told the game may close. Avoid another positioning request until a concrete diagnostic is ready.
