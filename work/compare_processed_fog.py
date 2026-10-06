"""Retain numeric fog-block differences between stable near/far captures."""
import json
from pathlib import Path
import struct

root=Path(__file__).resolve().parents[1]
directory=root/'work/live-atmosphere-readonly'
labels=('corson-position-check','corson-fog128-active','corson-fog512-active','corson-range-restored','corson-near-processed')
captures={label:json.loads(sorted(directory.glob('*-'+label+'.json'))[-1].read_text()) for label in labels}
far=captures[labels[0]]
fog=lambda j:bytes.fromhex(j['renderer_samples'][-1]['fog_110_19C_hex'])
baseline=fog(far)
out={'labels':{},'near_vs_far_float_changes':[]}
for label,capture in captures.items():
    raw=fog(capture)
    out['labels'][label]={'source_hash':capture.get('sha256',capture.get('block_sha256')),
        'position':capture['primary_view_candidates']['0x6739b10'].get('position_30_raw_floats'),
        'fog_110_19C':list(struct.unpack('<35f',raw)),
        'processed_endpoints':list(struct.unpack_from('<2f',raw,0x60)),
        'prepared_69C_724':list(struct.unpack('<34f',bytes.fromhex(capture['prepared_fog_context_69C_724_hex'])))}
near=fog(captures['corson-near-processed'])
for offset in range(0,len(baseline),4):
    if near[offset:offset+4]!=baseline[offset:offset+4]:
        out['near_vs_far_float_changes'].append({'render_offset':hex(0x110+offset),
            'corresponding_source_offset':hex(0x3EC+offset),
            'far':struct.unpack_from('<f',baseline,offset)[0],
            'near':struct.unpack_from('<f',near,offset)[0]})
path=root/'work/processed-fog-near-far-comparison.json'
path.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'labels':{k:{a:b for a,b in v.items() if a not in ('fog_110_19C','prepared_69C_724')} for k,v in out['labels'].items()},
                  'changes':out['near_vs_far_float_changes']},indent=2))
