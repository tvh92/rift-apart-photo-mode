"""Prepare a longer short clip to test startup initialization timing."""
import hashlib, json, runpy, struct, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'outputs/startup-repair'
state = json.loads((OUT/'direct-archive/state.json').read_text())
records = []
package = OUT/'NoIntro-2Second-CurrentBuild.stage'
with zipfile.ZipFile(package, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    z.writestr('info.json', json.dumps({'game':'RCRA','format_version':2,
        'name':'Short intro (2-second initialization test)','author':'Local compatibility test',
        'description':'First 60 original frames with original codec/audio metadata and original asset lengths.'}, indent=2))
    for row in state['rows']:
        data = (OUT/'direct-archive'/row['backup']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == row['original_sha256']
        frames = struct.unpack_from('<I', data, 8)[0]
        audio = struct.unpack_from('<I', data, 40)[0]
        assert audio == 2 and frames > 60
        index = 48+12*audio
        offsets = list(struct.unpack_from('<'+str(frames+1)+'I', data, index))
        keep = 60
        delta = 4*(frames-keep)
        new_offsets = [x-delta for x in offsets[:keep+1]]
        new_offsets[-1] &= ~1
        start, stop = offsets[0]&~1, offsets[keep]&~1
        clip = bytearray(data[:index]) + struct.pack('<'+str(keep+1)+'I', *new_offsets) + data[start:stop]
        largest = max((offsets[i+1]&~1)-(offsets[i]&~1) for i in range(keep))
        struct.pack_into('<4I', clip, 4, len(clip)-8, keep, largest, keep)
        assert clip[20:index] == data[20:index]
        assert len(clip) == new_offsets[-1]
        payload = clip + b'\0'*(len(data)-len(clip))
        z.writestr('0/'+row['id'], payload)
        records.append({'asset':row['id'],'frames':keep,'seconds':keep*struct.unpack_from('<I',clip,32)[0]/struct.unpack_from('<I',clip,28)[0],
            'audio_tracks':audio,'asset_bytes':len(payload),'bink_bytes':len(clip),'sha256':hashlib.sha256(payload).hexdigest()})
        if row['id'] == '905EBDB8C12D66E0':
            test = ROOT/'work/overstrike-audit/two-second-test.bk2'
            test.write_bytes(payload)
decoder = runpy.run_path(str(ROOT/'work/direct_intro_archive.py'))['decode_test'](test, 60)
assert not decoder['decoder_error']
report = {'package':package.name,'package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),
    'assets':records,'decoder_test':decoder,'hypothesis':'Four frames may end before native movie initialization transitions to playing. Not established.'}
(OUT/'two-second-preparation.json').write_text(json.dumps(report, indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='decoder_test'}, indent=2))
