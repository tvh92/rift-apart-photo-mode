import runpy,re
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py');D,Decoder=r['DATA'],r['Decoder'];text=next(x for x in r['SECTIONS'] if x[0]==b'.text');_,va,vs,rp,rs=text
insns=list(Decoder(64,D[rp:rp+rs],ip=va)); candidates=[]
for i,ins in enumerate(insns):
 s=r['Formatter'](r['FormatterSyntax'].NASM).format(ins)
 if ins.memory_displacement not in (0xA48,0xA50,0xA58):continue
 # find nearby register-indirect calls after a load from a candidate object field
 if not (s.lower().startswith(('mov ','movss ')) and '[' in s):continue
 dst=s.split(' ',1)[1].split(',',1)[0].strip().lower()
 if dst.startswith('qword ptr'):continue
 window=insns[i+1:i+8]; calls=[]
 for q in window:
  t=r['Formatter'](r['FormatterSyntax'].NASM).format(q).lower()
  if 'call ' in t and (dst in t or 'call qword [' in t): calls.append(t)
 if calls:
  b,e=r['bounds'](ins.ip); candidates.append((ins.ip,ins.memory_displacement,b,e,s,calls))
out=Path('work/lod_pc_trace/callback_load_call_candidates.txt')
with out.open('w') as f:
 f.write(f'candidates {len(candidates)}\n')
 for ip,d,b,e,s,calls in candidates:
  f.write(f'\n{ip:#x} field={d:#x} function={b:#x}-{e:#x}: {s}\n')
  f.write('\n'.join('  '+x for x in calls)+'\n')
print(out.resolve(),'candidates=',len(candidates))
