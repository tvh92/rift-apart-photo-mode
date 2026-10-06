from pathlib import Path
import struct

p = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\RiftApart.exe')
d = p.read_bytes()
pe = struct.unpack_from('<I', d, 0x3c)[0]
ns = struct.unpack_from('<H', d, pe + 6)[0]
osz = struct.unpack_from('<H', d, pe + 20)[0]
base = struct.unpack_from('<Q', d, pe + 48)[0]
secs = []
for i in range(ns):
    q = pe + 24 + osz + 40 * i
    nm = d[q:q + 8].split(b'\0')[0]
    vs, va, rs, rp = struct.unpack_from('<4I', d, q + 8)
    secs.append((nm, va, vs, rp, rs))

def to_rva(file_off):
    for _, va, _, rp, rs in secs:
        if rp <= file_off < rp + rs:
            return va + file_off - rp
    raise ValueError(hex(file_off))

def to_off(rva):
    for _, va, _, rp, rs in secs:
        if va <= rva < va + rs:
            return rp + rva - va
    raise ValueError(hex(rva))

def refs(dword):
    pat = struct.pack('<I', dword)
    out = []
    for nm, _, _, rp, rs in secs:
        if nm not in (b'.rdata', b'.data'):
            continue
        i = d.find(pat, rp, rp + rs)
        while i >= 0:
            if (i - rp) % 4 == 0:
                out.append(to_rva(i))
            i = d.find(pat, i + 1, rp + rs)
    return out

def is_text_ptr(ptr):
    if not base <= ptr < base + 0x8000000:
        return False
    r = ptr - base
    return any(nm == b'.text' and va <= r < va + rs for nm, va, _, _, rs in secs)

targets = [
    '.?AVAttachedLightData@@',
    '.?AVAttachedSpotlight@@',
    '.?AVAttachedSpotlightPrius@@',
]
for name in targets:
    ix = d.find(name.encode() + b'\0')
    if ix < 0:
        print('\nTYPE MISSING', name)
        continue
    td = to_rva(ix) - 16
    print('\nTYPE', name, 'TD', hex(td))
    cols = set()
    for tdref in refs(td):
        # A TypeDescriptor can be referenced by a BaseClassDescriptor.
        bcd = tdref
        try:
            b = struct.unpack('<7I', d[to_off(bcd):to_off(bcd) + 28])
            if b[0] == td and b[6] and b[6] < 0x8000000:
                chd = b[6]
                # COLs repeat the TypeDescriptor and CHD RVAs at +12/+16.
                for col in refs(td):
                    if col < 12:
                        continue
                    candidate = col - 12
                    try:
                        sig, ob, cd, td2, chd2, selfref = struct.unpack('<6I', d[to_off(candidate):to_off(candidate) + 24])
                    except Exception:
                        continue
                    if sig == 1 and td2 == td and chd2 == chd:
                        cols.add(candidate)
        except Exception:
            pass
    for col in sorted(cols):
        # Locate the absolute COL pointer stored immediately before each vtable.
        pat = struct.pack('<Q', base + col)
        for nm, _, _, rp, rs in secs:
            if nm not in (b'.rdata', b'.data'):
                continue
            pos = d.find(pat, rp, rp + rs)
            while pos >= 0:
                vt = to_rva(pos) + 8
                funcs = []
                for j in range(80):
                    ptr = struct.unpack_from('<Q', d, to_off(vt + 8 * j))[0]
                    if not is_text_ptr(ptr):
                        break
                    funcs.append(ptr - base)
                if funcs:
                    print(' COL', hex(col), 'VT', hex(vt), 'methods', [(i, hex(x)) for i, x in enumerate(funcs)])
                pos = d.find(pat, pos + 1, rp + rs)
