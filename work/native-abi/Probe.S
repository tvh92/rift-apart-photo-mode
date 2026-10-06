.intel_syntax noprefix
.text
.globl TestOriginal
TestOriginal:
mov [rip+observed_registers+0],rax
mov [rip+observed_registers+8],rcx
mov [rip+observed_registers+16],rdx
mov [rip+observed_registers+24],r8
mov [rip+observed_registers+32],r9
mov [rip+observed_registers+40],r10
mov [rip+observed_registers+48],r11
movdqu [rip+observed_xmm+0],xmm0
movdqu [rip+observed_xmm+16],xmm1
movdqu [rip+observed_xmm+32],xmm2
movdqu [rip+observed_xmm+48],xmm3
movdqu [rip+observed_xmm+64],xmm4
movdqu [rip+observed_xmm+80],xmm5
pushfq
pop rax
mov [rip+observed_flags],rax
mov rax,rsp
and eax,15
mov [rip+original_alignment],rax
mov eax,1234
ret
.globl CaptureFree
.globl UpdateMotion
.globl ClearPhotoLOD
.globl EnsureProxy
CaptureFree:
UpdateMotion:
EnsureProxy:
ClearPhotoLOD:
mov rax,rsp
and eax,15
mov [rip+callback_alignment],rax
mov rax,0xaabbccdd
mov [rsp+8],rax
mov [rsp+16],rax
mov [rsp+24],rax
mov [rsp+32],rax
xor rax,rax
xor rcx,rcx
xor rdx,rdx
xor r8,r8
xor r9,r9
xor r10,r10
xor r11,r11
pxor xmm0,xmm0
pxor xmm1,xmm1
pxor xmm2,xmm2
pxor xmm3,xmm3
pxor xmm4,xmm4
pxor xmm5,xmm5
clc
ret
.globl TestFree
.seh_proc TestFree
TestFree:
sub rsp,40
.seh_stackalloc 40
.seh_endprologue
movdqu xmm0,[rip+input_xmm]
movdqu xmm1,[rip+input_xmm]
movdqu xmm2,[rip+input_xmm]
movdqu xmm3,[rip+input_xmm]
movdqu xmm4,[rip+input_xmm]
movdqu xmm5,[rip+input_xmm]
mov rax,4369
mov rcx,8738
mov rdx,13107
mov r8,17476
mov r9,21845
mov r10,26214
mov r11,30583
stc
call HookFreeStub
add rsp,40
ret
.seh_endproc
.globl TestMotion
.seh_proc TestMotion
TestMotion:
sub rsp,40
.seh_stackalloc 40
.seh_endprologue
movdqu xmm0,[rip+input_xmm]
movdqu xmm1,[rip+input_xmm]
movdqu xmm2,[rip+input_xmm]
movdqu xmm3,[rip+input_xmm]
movdqu xmm4,[rip+input_xmm]
movdqu xmm5,[rip+input_xmm]
mov rax,4369
mov rcx,8738
mov rdx,13107
mov r8,17476
mov r9,21845
mov r10,26214
mov r11,30583
stc
call HookMotionStub
add rsp,40
ret
.seh_endproc
.globl TestForward
.seh_proc TestForward
TestForward:
sub rsp,40
.seh_stackalloc 40
.seh_endprologue
movdqu xmm0,[rip+input_xmm]
movdqu xmm1,[rip+input_xmm]
movdqu xmm2,[rip+input_xmm]
movdqu xmm3,[rip+input_xmm]
movdqu xmm4,[rip+input_xmm]
movdqu xmm5,[rip+input_xmm]
mov rax,4369
mov rcx,8738
mov rdx,13107
mov r8,17476
mov r9,21845
mov r10,26214
mov r11,30583
stc
call HidForward0
add rsp,40
ret
.seh_endproc

.globl TestPhotoDestroy
.seh_proc TestPhotoDestroy
TestPhotoDestroy:
sub rsp,40
.seh_stackalloc 40
.seh_endprologue
movdqu xmm0,[rip+input_xmm]
movdqu xmm1,[rip+input_xmm]
movdqu xmm2,[rip+input_xmm]
movdqu xmm3,[rip+input_xmm]
movdqu xmm4,[rip+input_xmm]
movdqu xmm5,[rip+input_xmm]
mov rax,4369
mov rcx,8738
mov rdx,13107
mov r8,17476
mov r9,21845
mov r10,26214
mov r11,30583
stc
call HookPhotoDestroyStub
add rsp,40
ret
.seh_endproc

.globl TestPhotoCleanup
.seh_proc TestPhotoCleanup
TestPhotoCleanup:
sub rsp,40
.seh_stackalloc 40
.seh_endprologue
movdqu xmm0,[rip+input_xmm]
movdqu xmm1,[rip+input_xmm]
movdqu xmm2,[rip+input_xmm]
movdqu xmm3,[rip+input_xmm]
movdqu xmm4,[rip+input_xmm]
movdqu xmm5,[rip+input_xmm]
mov rax,4369
mov rcx,8738
mov rdx,13107
mov r8,17476
mov r9,21845
mov r10,26214
mov r11,30583
stc
call HookPhotoCleanupStub
add rsp,40
ret
.seh_endproc
