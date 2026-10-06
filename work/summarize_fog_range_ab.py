"""Compare saved read-only captures and completed temporary-test reports."""
import json
from pathlib import Path
import struct

root=Path(__file__).resolve().parents[1]
directory=root/'work/live-atmosphere-readonly'
result={'user_observations':{'128':'No visible change','512':'No visible change'},
        'conclusion':'Neither tested endpoint visibly corrects the white pit fog. Do not install a range-only fix.',
        'captures':{},'completed_probes':[]}
for label in ('corson-position-check','corson-fog128-active','corson-fog512-active'):
    path=sorted(directory.glob('*-'+label+'.json'))[-1]
    capture=json.loads(path.read_text(encoding='utf-8'))
    source=path.with_suffix('.bin').read_bytes()
    prepared=bytes.fromhex(capture['prepared_fog_context_69C_724_hex'])
    result['captures'][label]={'evidence':str(path),'camera':capture['primary_view_candidates']['0x6739b10'],
       'source_depth_endpoints':struct.unpack_from('<2f',source,0x44C),
       'processed_depth_endpoints':[struct.unpack_from('<2f',bytes.fromhex(v['block_hex']),0x170)
                                    for v in capture['renderer_samples']],
       'prepared_grid_z_6AC':struct.unpack_from('<4f',prepared,0x10),
       'prepared_height_fade_6BC':struct.unpack_from('<4f',prepared,0x20)}
for path in sorted(directory.glob('*-fog-range-probe.json')):
    probe=json.loads(path.read_text(encoding='utf-8'))
    if probe['applied']:
        result['completed_probes'].append({'evidence':str(path),**probe})
target=root/'work/fog-range-ab-result.json'
target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
