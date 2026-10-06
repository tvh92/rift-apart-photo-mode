"""Generate ABI-preserving forwarding/hooks from the real Windows HID exports."""
import struct,json
from pathlib import Path
root=Path(__file__).resolve().parent.parent
out=root/'outputs/camera-native'
data=Path(r'C:\Windows\System32\hid.dll').read_bytes()
pe=struct.unpack_from('<I',data,0x3c)[0];ns=struct.unpack_from('<H',data,pe+6)[0];optsz=struct.unpack_from('<H',data,pe+20)[0]
assert struct.unpack_from('<H',data,pe+4)[0]==0x8664
sections=[]
for i in range(ns):
 p=pe+24+optsz+40*i;vs,va,rs,rp=struct.unpack_from('<4I',data,p+8);sections.append((va,max(vs,rs),rp))
def off(rva):
 for va,size,rp in sections:
  if va<=rva<va+size:return rp+rva-va
 raise ValueError(hex(rva))
rva,size=struct.unpack_from('<II',data,pe+24+112)
_,_,_,_,_,base,nfunctions,nnames,function_table,name_table,ordinal_table=struct.unpack_from('<IIHH7I',data,off(rva))
names={}
for i in range(nnames):
 nrva=struct.unpack_from('<I',data,off(name_table)+4*i)[0];p=off(nrva)
 name=data[p:data.index(0,p)].decode('ascii');ordinal=struct.unpack_from('<H',data,off(ordinal_table)+2*i)[0]
 names[ordinal]=name
exports=[]
for i in range(nfunctions):
 if struct.unpack_from('<I',data,off(function_table)+4*i)[0]:exports.append((base+i,names.get(i)))
assert exports and all(name is None or name.replace('_','').isalnum() for _,name in exports)
asm=['.intel_syntax noprefix','.text']
def stub(name,callback,target):
 lines=[f'.globl {name}',f'.def {name}; .scl 2; .type 32; .endef',f'.seh_proc {name}',f'{name}:','pushfq','.seh_stackalloc 8']
 for reg in ['rax','rcx','rdx','r8','r9','r10','r11']:lines += [f'push {reg}','.seh_stackalloc 8']
 lines += ['sub rsp,136','.seh_stackalloc 136','.seh_endprologue']
 for i in range(6):lines.append(f'movdqu [rsp+{32+16*i}],xmm{i}')
 lines.append(f'call {callback}')
 for i in range(6):lines.append(f'movdqu xmm{i},[rsp+{32+16*i}]')
 lines.append('add rsp,136')
 for reg in ['r11','r10','r9','r8','rdx','rcx','rax']:lines.append(f'pop {reg}')
 lines+=['popfq',f'jmp qword ptr [rip+{target}]','.seh_endproc']
 return lines
definitions=['LIBRARY hid','EXPORTS']
for i,(ordinal,name) in enumerate(exports):
 symbol=f'HidForward{i}';asm+=stub(symbol,'EnsureProxy',f'hid_targets+{i*8}')
 definitions.append(f'  {name if name else symbol}={symbol} @{ordinal}'+(' NONAME' if name is None else ''))
asm+=stub('HookFreeStub','CaptureFree','original_free')
asm+=stub('HookMotionStub','UpdateMotion','original_motion')
(out/'CameraStubs.S').write_text('\n'.join(asm)+'\n')
(out/'hid.def').write_text('\n'.join(definitions)+'\n')
(out/'HidExports.c').write_text('const char *hid_names[]={' + ','.join(json.dumps(name) if name else '0' for _,name in exports)+'};\nconst unsigned short hid_ordinals[]={' + ','.join(str(ordinal) for ordinal,_ in exports)+'};\n')
(out/'export-manifest.json').write_text(json.dumps({'system_hid_exports':exports,'count':len(exports)},indent=2)+'\n')
print('Generated',len(exports),'HID export forwarders and two camera hook stubs.')
