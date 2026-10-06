# Proven renderer fog parameter and texture copy

Read-only evidence from the exact supported local executable. Detailed native disassembly is in `work/light-copy-candidates-main.txt` (11D3500) and `work/disassemble_camera.py` can reproduce it. No installed shader, asset, native DLL or runtime field changed.

## Active atmosphere to renderer bridge

Caller12BB7B9..12BBA56 asks FB1130 with registry52DDA20 and the actual view index `[rdi+F90]` at12BB83C..12BB84A. It may select an explicit atmosphere override from `[rsi+48]`. At12BB875..12BB881 it passes the chosen atmosphere asR8 into11D3500, alongside the render viewRCX, auxiliary stateRDX and flag bitsR9D.

11D3500 stores R8 inRBX; at11D38AB..11D38B5 it chooses the source atmosphere intoRSI. Flag bit7 or global5339340 can select null/default postprocess values. The exact flag/global meanings are unproven; do not patch them.

RSI+3EC..474 is copied into a render-state blockR14+110..198 at11D396B..11D39E1. The named fog-map handlesRSI+480/+498, checked for resource tag11 at+488/+4A0, are resolved through11D60F0 into destination texture recordsR14+348/+380 at11D3B46..11D3B92. This links the named texture handles to an actual renderer-state consumer, not a serialization copy. Null/default path11D3B9C callsFB6770 onR14+110 and clears/falls back texture records.

FB6770 initializes the compact fog block with whiteRGBA at+0..C and height/opacity default patterns (including -100,100,200,300,400). These are exact native defaults, not evidence that the reported white fog takes this path. Near and far camera captures must test the source pointer, flag choice, texture handles and fog scalar values. Parent DDL offsets still do not directly label the compact fields.

Other copies in the same consumer: source+4A8 -> dest+19C; +4AC..4B8 -> +1A0..1AC; +4C0..4E0 -> +1B0..1D0; +524..53C -> +1D8..1F0; +3D8..3E8 -> +22C..23C. Scalars+540/+544 feed view/projection rebuild through1213240/1214150 when limits differ. Their default.1/1000 and projection code make them unsuitable to label as fog distances from proximity alone.

## Next evidence

Capture current atmosphere and actual renderer-selected atmosphere near/far in Corson V Photo Mode. Determine whether white fog correlates with default source, regional/override atmosphere selection, missing/unresolved texture records, fog-map parameters or shader depth/mip calculation. `work/capture_live_atmosphere.py` safely captures registry slot0, but renderer uses view+F90; this difference must be considered. No fog override is justified yet.
