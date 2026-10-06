import re
from native_trace_full import r

for name, va, vs, rp, rs in r['SECTIONS']:
    if name not in (b'.rdata', b'.data'):
        continue
    for match in re.finditer(rb'[ -~]{5,}\x00', r['DATA'][rp:rp+rs]):
        value = match.group()[:-1].decode('ascii')
        if re.search(r'fog|volum|light.*(cull|fade|render|submit|distance)|(?:cull|fade|render|submit|distance).*light', value, re.I):
            print(f'{va+match.start():08X} {value}')
