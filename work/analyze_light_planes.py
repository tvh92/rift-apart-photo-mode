"""Offline: test captured light records against captured request planes.

Reads a capture JSON from capture_photo_lights_readonly.py (with request
planes). For each listed source pointer, transforms its local box
(+40 centre, +50 half-extents) by the record rows (+00/+10/+20 axes,
+30 translation) and reports the signed box distance per plane, as in
0x12B72A0: a box is outside a plane when n.c + d + sum|n.axis_i|*e_i < 0.
"""
import argparse
import json
from pathlib import Path
import struct


def world_box(raw):
    rows = [struct.unpack_from('<3f', raw, off) for off in (0, 0x10, 0x20, 0x30)]
    centre = struct.unpack_from('<3f', raw, 0x40)
    extent = struct.unpack_from('<3f', raw, 0x50)
    world = [sum(centre[i] * rows[i][k] for i in range(3)) + rows[3][k] for k in range(3)]
    axes = [[rows[i][k] * extent[i] for k in range(3)] for i in range(3)]
    return world, axes


def box_margin(plane, world, axes):
    n, d = plane[:3], plane[3]
    if None in plane:
        return None
    centre = sum(a * b for a, b in zip(n, world)) + d
    reach = sum(abs(sum(a * b for a, b in zip(n, axis))) for axis in axes)
    return centre + reach


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('sources', nargs='+')
    args = parser.parse_args()
    data = json.loads(args.capture.read_text())
    sample = next(s for s in data['samples'] if s['queries'])
    query = sample['queries'][0]
    fixed = next(r for r in query['requests'] if r['kind'] == 'fixed')
    known = dict(query['sources'])
    for request in query['requests']:
        known.update(request['worker_output']['sources'])
    report = {'camera': sample['position_30'], 'view_clip': sample.get('view_clip'), 'sources': {}}
    for text in args.sources:
        if text not in known or 'raw_hex' not in known[text]:
            report['sources'][text] = {'error': 'Source prefix not in capture'}
            continue
        world, axes = world_box(bytes.fromhex(known[text]['raw_hex']))
        margins = [box_margin(p, world, axes) for p in fixed['planes']]
        outside = [i for i, m in enumerate(margins) if m is not None and m < 0]
        report['sources'][text] = {
            'in_fixed_input': text in query['arrays']['input_fixed']['pointers'],
            'box_centre': world, 'outside_planes': outside,
            'margins': [None if m is None else round(m, 3) for m in margins]}
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
