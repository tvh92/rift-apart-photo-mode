"""Read embedded DXBC RDEF buffer names/variable offsets from the local EXE."""
import json
import struct
from pathlib import Path
from native_trace_full import r

data = r['DATA']
results = []
cursor = 0
while True:
    cursor = data.find(b'DXBC', cursor)
    if cursor < 0:
        break
    start = cursor
    cursor += 4
    try:
        version,total,count = struct.unpack_from('<III',data,start+20)
        if version != 1 or count > 32 or total > 2000000 or start+total > len(data):
            continue
        for offset in struct.unpack_from('<'+'I'*count,data,start+32):
            chunk = start+offset
            if data[chunk:chunk+4] != b'RDEF':
                continue
            length = struct.unpack_from('<I',data,chunk+4)[0]
            blob = data[chunk+8:chunk+8+length]
            if b'Fog' not in blob:
                continue
            def string(off):
                return blob[off:blob.index(0,off)].decode('ascii')
            def members(type_offset, base_offset=0, prefix='', depth=0):
                if depth > 8:
                    return []
                cls,typ,rows,cols,elements,nmembers,member_offset = struct.unpack_from('<6HI',blob,type_offset)
                output = []
                for m in range(nmembers):
                    member_name,member_type,member_start = struct.unpack_from('<III',blob,member_offset+m*12)
                    label = prefix+string(member_name)
                    output.append({'name':label,'offset':base_offset+member_start})
                    output.extend(members(member_type,base_offset+member_start,label+'.',depth+1))
                return output
            cbcount,cboffset = struct.unpack_from('<II',blob)
            buffers = []
            for index in range(cbcount):
                name,variables,varoffset,size,flags,kind = struct.unpack_from('<6I',blob,cboffset+index*24)
                fields = []
                for v in range(variables):
                    vname,vstart,vsize,vflags,vtype,vdefault,*rest = struct.unpack_from('<10I',blob,varoffset+v*40)
                    fields.append({'name':string(vname),'offset':vstart,'size':vsize,'flags':vflags,
                                   'members':members(vtype,vstart,string(vname)+'.')})
                buffers.append({'name':string(name),'size':size,'fields':fields})
            results.append({'file_offset':hex(start),'size':total,'buffers':buffers})
    except (ValueError,struct.error,UnicodeDecodeError):
        continue
Path('work/shader-fog-reflection-main.json').write_text(json.dumps(results,indent=2)+'\n')
print('Fog shaders',len(results))
seen = set()
for shader in results:
    for buffer in shader['buffers']:
        key = (buffer['name'],buffer['size'])
        if key in seen:
            continue
        seen.add(key)
        print('BUFFER',key)
        for field in buffer['fields']:
            if 'fog' in field['name'].lower() or 'volumetric' in buffer['name'].lower():
                print(field)
            else:
                for member in field['members']:
                    if 'fog' in member['name'].lower():
                        print(member)
