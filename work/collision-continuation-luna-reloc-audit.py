import runpy,struct,sys
from pathlib import Path
r=runpy.run_path('work/disassemble_camera.py')
from iced_x86 import Decoder,Formatter,FormatterSyntax,FlowControl
start,end=r['bounds'](0x1A5EBA0)
row=next(x for x in r['PDATA'] if x[0]==start and x[1]==end)
uoff=row[2]
print('function',hex(start),hex(end),'len',hex(end-start),'unwind_rva',hex(uoff),'unwind_fileoff',hex(r['offset'](uoff)))
b=r['bytes_at'](uoff,64)
print('unwind_raw',b[:24].hex(' '))
verflags,prolog,count,frame=b[:4]
print('unwind_version',verflags&7,'flags',verflags>>3,'prolog_size',prolog,'code_slots',count,'frame_reg',frame&15,'frame_offset_units',frame>>4)
slotbytes=count*2; trailer=((slotbytes+3)//4)*4
print('unwind_codes',b[4:4+slotbytes].hex(' '),'trailer',b[4+trailer:4+trailer+24].hex(' '))
fmt=Formatter(FormatterSyntax.NASM)
ins=list(Decoder(64,r['bytes_at'](start,end-start),ip=start))
print('instruction_count',len(ins))
for i in ins:
 s=[]
 if i.is_ip_rel_memory_operand:s.append('RIP='+hex(i.ip_rel_memory_address))
 if i.flow_control not in (FlowControl.NEXT,):
  if i.flow_control in (FlowControl.CALL,FlowControl.UNCONDITIONAL_BRANCH,FlowControl.CONDITIONAL_BRANCH,FlowControl.XBEGIN_XABORT_XEND):
   try:s.append('FLOW='+str(i.flow_control)+' TARGET='+hex(i.near_branch_target))
   except: s.append('FLOW='+str(i.flow_control))
  else:s.append('FLOW='+str(i.flow_control))
 if s:print(hex(i.ip),fmt.format(i),' | '.join(s))
