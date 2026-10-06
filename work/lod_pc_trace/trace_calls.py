import runpy, struct, json
from pathlib import Path
r = runpy.run_path('work/disassemble_camera.py')
D, Decoder = r['DATA'], r['Decoder']
BASE, SECTIONS = r['BASE'], r['SECTIONS']
# Scan the executable's .text instructions for direct calls/jumps into the validator.
text = next(x for x in SECTIONS if x[0] == b'.text')
name, va, vs, rp, rs = text
refs=[]
for ins in Decoder(64, D[rp:rp+rs], ip=va):
    if ins.is_call_near or ins.is_jmp_near:
        if ins.near_branch_target == 0x168ad40:
            refs.append((ins.ip, ins.near_branch_target, ins.len))
# Disassemble each NxSettingsImpl vtable method and keep lines indicating relevant dataflow.
vts=json.loads(Path('work/lod-native-vtables.json').read_text())['NxSettingsImpl@nx'][0]['vtables'][0]['methods']
F=Path('work/lod_pc_trace/nxsettings-validator-callers.txt')
with F.open('w',encoding='utf-8') as f:
    f.write('Direct xrefs to PC settings validator 0x168ad40 (call/jmp):\n')
    for ip,t,n in refs: f.write(f'{ip:#x} -> {t:#x} len={n}\n')
    f.write(f'\nNxSettingsImpl vtable methods: {len(vts)}\n')
    for a in vts:
        a = int(a, 0) if isinstance(a, str) else a
        f.write(f'\nFUNCTION {a:#x} bounds {tuple(hex(x) for x in r["bounds"](a))}\n')
        for ip,line in r['disassemble'](a):
            low=line.lower()
            if any(k in low for k in ['[rsi+70h]','[rbx+70h]','[rcx+70h]','[rdx+70h]','[rax+70h]','+70h','168ad40','call ','jmp ']):
                f.write(f'{ip:08x} {line}\n')
print(F.resolve())
print('validator refs:', [hex(x[0]) for x in refs])
