"""Prepare two comparable diagnostic packages without changing game files."""
import hashlib, json, runpy, struct, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'outputs/startup-repair'
DIRECT = OUT/'direct-archive'
state = json.loads((DIRECT/'state.json').read_text())
GAME = Path(state['archive']).parent.parent
assert hashlib.sha1((GAME/'toc').read_bytes()).hexdigest() == state['toc_bak_sha1'], 'Game index is not pristine'
packages = {
    'Intro-Original-Routing-Test.stage': {'name': 'Original intro routing test', 'short': False},
    'NoIntro-Padded-CurrentBuild.stage': {'name': 'Short intro with original-sized assets', 'short': True}}
report = {}
for filename, options in packages.items():
    path = OUT/filename
    records = []
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr('info.json', json.dumps({'game': 'RCRA', 'format_version': 2,
            'name': options['name'], 'author': 'Local compatibility test',
            'description': 'Diagnostic from locally verified game files. No runtime code.'}, indent=2))
        with Path(state['archive']).open('rb') as f:
            for row in state['rows']:
                f.seek(row['offset'])
                original = f.read(row['length'])
                assert hashlib.sha256(original).hexdigest() == row['original_sha256']
                if options['short']:
                    clip = (ROOT/'work/short-intro'/(row['id']+'.bk2')).read_bytes()
                    assert clip[:4] == original[:4] == b'KB2j'
                    assert struct.unpack_from('<I', clip, 8)[0] == 4
                    assert struct.unpack_from('<I', clip, 40)[0] == 2
                    assert clip[20:72] == original[20:72], 'Codec/audio metadata changed'
                    payload = clip + b'\0'*(len(original)-len(clip))
                else:
                    payload = original
                assert len(payload) == row['length']
                z.writestr('0/'+row['id'], payload)
                records.append({'asset': row['id'], 'bytes': len(payload),
                    'sha256': hashlib.sha256(payload).hexdigest(),
                    'bink_declared_bytes': struct.unpack_from('<I', payload, 4)[0]+8,
                    'frames': struct.unpack_from('<I', payload, 8)[0],
                    'audio_tracks': struct.unpack_from('<I', payload, 40)[0]})
                if options['short'] and row['id'] == '905EBDB8C12D66E0':
                    (ROOT/'work/overstrike-audit/padded-decoder-test.bk2').write_bytes(payload)
    report[filename] = {'package_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'assets': records}
decode = runpy.run_path(str(ROOT/'work/direct_intro_archive.py'))['decode_test']
report['decoder_test'] = decode(ROOT/'work/overstrike-audit/padded-decoder-test.bk2')
assert report['decoder_test']['frames'] == 4 and not report['decoder_test']['decoder_error']
(OUT/'routing-test-preparation.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
