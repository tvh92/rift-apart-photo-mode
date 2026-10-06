"""Read-only research parser. Format references: Tkachov/ALERT DSAR and DAT1 docs.
Only outputs JSON in this workspace; game files are opened for reading.
"""
from pathlib import Path
import struct, io, json, re

GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart')
WORK = Path(__file__).resolve().parent

def lz4(data, expected):
    out = bytearray()
    p = 0
    while p < len(data):
        token = data[p]; p += 1
        literal = token >> 4
        if literal == 15:
            while True:
                n = data[p]; p += 1; literal += n
                if n != 255: break
        out.extend(data[p:p+literal]); p += literal
        if p == len(data): break
        offset = struct.unpack_from('<H', data, p)[0]; p += 2
        assert 0 < offset <= len(out)
        length = (token & 15) + 4
        if (token & 15) == 15:
            while True:
                n = data[p]; p += 1; length += n
                if n != 255: break
        # Overlapping back references repeat their existing prefix.
        prefix = out[-offset:]
        out.extend((prefix * ((length + offset - 1) // offset))[:length])
        assert len(out) <= expected
    assert len(out) == expected
    return out

def dsar(path):
    data = path.read_bytes()
    magic, version, count, header_end, total = struct.unpack_from('<4IQ', data)
    assert magic == 0x52415344 and version == 0x10003
    out = bytearray(total)
    for i in range(count):
        start, pos, size, compressed, kind = struct.unpack_from('<2Q2IB', data, 32+32*i)
        assert kind == 3
        out[start:start+size] = lz4(data[pos:pos+compressed], size)
    return out

def sections(data):
    magic, kind, size, count, unknown = struct.unpack_from('<IIIHH', data)
    assert magic == 0x44415431 and size <= len(data)
    return {tag: (pos, n) for tag, pos, n in
            [struct.unpack_from('<III', data, 16+12*i) for i in range(count)]}

def decode(asset, section, locations=None):
    f = io.BytesIO(section)
    def unpack(fmt):
        return struct.unpack(fmt, f.read(struct.calcsize(fmt)))
    def align():
        f.seek((f.tell()+3)//4*4)
    def string_at(p):
        end = asset.index(0, p)
        return asset[p:end].decode('utf-8')
    def node(t, path):
        fmt = {0:'<B',1:'<H',2:'<I',4:'<b',5:'<h',6:'<i',8:'<f',17:'<Q'}
        if t in fmt: return unpack(fmt[t])[0]
        if t == 15: return bool(unpack('<B')[0])
        if t == 19: f.read(1); return None
        if t == 13: return obj(path)
        if t == 10:
            length, h32, h64 = unpack('<IIQ')
            value = f.read(length).decode('utf-8'); assert f.read(1) == b'\0'
            align(); return value
        raise ValueError(f'Unknown type {t}')
    def obj(path=''):
        zero, version, count, length = unpack('<4I')
        assert zero == 0 and version == 0x03150044 and count < 100000
        start = f.tell()
        entries = [unpack('<IHBB') for _ in range(count)]
        names = [string_at(unpack('<I')[0]) for _ in range(count)]
        result = {}
        for entry_index, (name, (_, flags, _, t)) in enumerate(zip(names, entries)):
            n = flags >> 4
            field_path = path+'.'+name
            if locations is not None:
                locations[field_path] = {'type':t, 'offset':f.tell(), 'count':n,
                                         'type_offset':start+8*entry_index+7,
                                         'last_field':entry_index == count-1,
                                         'object_end':start+length}
            values = [node(t, field_path if n == 1 else field_path+f'[{i}]') for i in range(n)]
            result[name] = values[0] if n == 1 else values
        align()
        assert f.tell() <= start+length
        f.seek(start+length)
        return result
    return obj()

archive = dsar(GAME/'d'/'config')
toc = (GAME/'toc').read_bytes()
ts = sections(toc[8:])
ap, an = ts[0x398ABFF0]
archives = toc[8+ap:8+ap+an]
archive_names = [archives[i:i+40].split(b'\0',1)[0].decode('ascii') for i in range(0, an, 66)]
config_archive_id = archive_names.index('d\\config')
mp, mn = ts[0x65BCF461]
ip, inn = ts[0x506D7B8A]
metadata = {}
for i in range(mn//16):
    size, archive_id, offset, header = struct.unpack_from('<IIIi', toc, 8+mp+16*i)
    if archive_id == config_archive_id:
        aid = struct.unpack_from('<Q', toc, 8+ip+8*i)[0]
        metadata[offset] = {'asset_id':f'{aid:016X}', 'toc_index':i, 'toc_size':size, 'toc_header_offset':header}
matches = []
parsed = 0
for match in re.finditer(b'1TAD', archive):
    start = match.start()
    try:
        size = struct.unpack_from('<I', archive, start+8)[0]
        asset = archive[start:start+size]
        ss = sections(asset)
        if 0x4A128222 not in ss or 0xE501186F not in ss: continue
        p, n = ss[0x4A128222]
        typ = decode(asset, asset[p:p+n])
        parsed += 1
        if re.search('Perf|LOD|Render|Streaming', str(typ)):
            if typ.get('Type') == 'PerfSpecConfig':
                p, n = ss[0xE501186F]
                perf = decode(asset, asset[p:p+n])
                (WORK/'perf_spec.json').write_text(json.dumps(perf, indent=2), encoding='utf-8')
                print('PERF CONFIG', start, metadata.get(start) or metadata.get(start-36))
        if 'photo' not in str(typ).lower(): continue
        p, n = ss[0xE501186F]
        content = decode(asset, asset[p:p+n])
        record = {'archive_offset': start, 'size': size, 'type': typ, 'content': content}
        record['toc'] = metadata.get(start) or metadata.get(start-36)
        matches.append(record)
        (WORK/f'config_{start:08x}.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    except (AssertionError, ValueError, struct.error, IndexError) as e:
        print('Rejected candidate', start, type(e).__name__, str(e))
print('Parsed config headers:', parsed, 'Photo config count:', len(matches))
for record in matches:
    print('PHOTO CONFIG', record['archive_offset'], record['type'], record['toc'])
    def walk(value, path=''):
        if isinstance(value, dict):
            for k,v in value.items(): walk(v, path+'.'+k)
        elif isinstance(value, list):
            for i,v in enumerate(value): walk(v, path+f'[{i}]')
        elif re.search('Tether|FreeMove|Collis|Orbit|CamData|FarClip|LOD', path, re.I):
            print(path, '=', value)
    walk(record['content'])
