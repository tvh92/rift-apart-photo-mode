"""Compare observed CPU light records without asserting a final cull cause."""
from pathlib import Path
import argparse
import json
import math

root = Path(__file__).resolve().parents[1]


def position_key(record):
    return tuple(round(v, 3) for v in record['world_position_B0'])


def summarize(path):
    data = json.loads(path.read_text())
    assert data['writes'] == 0 and data['samples'], path
    samples = data['samples']
    sets = [{position_key(r) for r in s['records']} for s in samples]
    by_position = {}
    for sample in samples:
        for record in sample['records']:
            by_position.setdefault(position_key(record), []).append(record)
    return data, sets, by_position


def compare(near_path, far_path):
    near, near_sets, near_records = summarize(near_path)
    far, far_sets, far_records = summarize(far_path)
    near_common = set.intersection(*near_sets)
    far_union = set.union(*far_sets)
    rows = []
    # Spatial six-light arrangement near the red bridge. Identification remains
    # tentative until the same lights correlate with the visible transition.
    for key in sorted(near_common):
        x, y, z = key
        if not (-70 < x < -10 and 17.9 < y < 18.4 and 10 < z < 45):
            continue
        a = near_records[key][0]
        b = far_records.get(key, [])
        rows.append({
            'position': a['world_position_B0'],
            'near_sample_presence': sum(key in s for s in near_sets),
            'far_sample_presence': sum(key in s for s in far_sets),
            'near_rgb': a['rgb_70'],
            'far_rgb_values': sorted({tuple(r['rgb_70']) for r in b}),
            'far_max_rgb_difference': max((max(abs(n - f) for n, f in zip(a['rgb_70'], r['rgb_70'])) for r in b), default=None),
            'near_radius': a['attenuation_radius_DC'],
            'near_camera_distance': math.dist(a['world_position_B0'], near['samples'][0]['position_30']),
            'far_camera_distance': math.dist(a['world_position_B0'], far['samples'][0]['position_30']),
        })
    return {
        'near_file': str(near_path), 'far_file': str(far_path),
        'near_label': near['label'], 'far_label': far['label'],
        'near_camera': near['samples'][0]['position_30'], 'far_camera': far['samples'][0]['position_30'],
        'near_record_counts': [s['pass67_record_count'] for s in near['samples']],
        'far_record_counts': [s['pass67_record_count'] for s in far['samples']],
        'near_sample_object_errors': [len(s['errors']) for s in near['samples']],
        'far_sample_object_errors': [len(s['errors']) for s in far['samples']],
        'near_persistent_positions_absent_all_far': [list(k) for k in sorted(near_common - far_union)],
        'candidate_bridge_group': rows,
        'classification': 'Observed CPU submission-list membership changes. The candidate bridge group and exact rejection gate are not yet established as the visible cause.',
        'limits': [
            'World position matching is not a proven source-object identity.',
            'Raw queue totals are not final callback batch counts or GPU inclusion.',
            'Stable repeated headers do not make records atomic; storage can retire or be reused.',
            'Ctrl ON is supplied by the user; the reader does not verify the preference flag.',
            'No source query captured: passBB marker has null arguments; its frame job is returned separately.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('near', type=Path)
    parser.add_argument('far', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = compare(args.near, args.far)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'output': str(args.output), 'near_counts': report['near_record_counts'],
                      'far_counts': report['far_record_counts'], 'candidate_bridge_group': report['candidate_bridge_group']}, indent=2))


if __name__ == '__main__':
    main()
