"""Reversible diagnostic: keep the working TOC and replace only movie prefixes.

The Bink file header/index declares four frames and its own shorter file length.
The original archive ranges and TOC records remain unchanged. This isolates
archive redirection from the replacement video's compatibility with the game.
"""
import argparse, ast, ctypes as C, hashlib, json, os, struct, subprocess, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart')
OUT = ROOT / 'outputs/startup-repair/direct-archive'
STATE = OUT / 'state.json'
CLEAN_SHA1 = '64946f571579d9ea0a17e675682e2994dc0f20fc'
CAMERA_TOC_SHA1 = '4a79e804bf157ad4429e54c3db890ce681c2068c'
CLIP_SHA256 = 'c199732999d3d6cf5b0b9dae77361577a880a9421a6896b18262314a6891db96'
IDS = [0x851735C03E050852, 0x8B203B05CA2AEB50, 0x905EBDB8C12D66E0]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def closed():
    result = subprocess.run(['powershell', '-NoProfile', '-Command',
        'if (Get-Process RiftApart,Overstrike -ErrorAction SilentlyContinue) { exit 9 }'],
        capture_output=True)
    if result.returncode:
        raise RuntimeError('Close Rift Apart and Overstrike first.')

def guard_index():
    assert hashlib.sha1((GAME / 'toc.BAK').read_bytes()).hexdigest() == CLEAN_SHA1
    assert hashlib.sha1((GAME / 'toc').read_bytes()).hexdigest() == CAMERA_TOC_SHA1

def table():
    ns = {}
    tree = ast.parse((ROOT / 'work/inspect_photo_config.py').read_text())
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,
        (ast.Import, ast.ImportFrom, ast.FunctionDef))], type_ignores=[]), 'helpers', 'exec'), ns)
    data = (GAME / 'toc').read_bytes()
    sections = ns['sections'](data[8:])
    ip, size = sections[0x506D7B8A]
    mp, _ = sections[0x65BCF461]
    ap, size_a = sections[0x398ABFF0]
    ids = [x[0] for x in struct.iter_unpack('<Q', data[8+ip:8+ip+size])]
    archives = [data[8+ap+i:8+ap+i+40].split(b'\0')[0].decode()
        for i in range(0, size_a, 66)]
    rows = []
    for aid in IDS:
        size, ai, offset, header = struct.unpack_from('<IIIi', data, 8+mp+16*ids.index(aid))
        assert archives[ai].replace('\\', '/') == 'd/movie' and header == -1
        rows.append({'id': f'{aid:016X}', 'offset': offset, 'length': size})
    return rows

def read_range(f, row):
    f.seek(row['offset'])
    data = f.read(row['length'])
    assert len(data) == row['length']
    return data

def decode_test(path, expected_frames=4):
    dll = C.WinDLL(str(GAME / 'bink2w64.dll'), winmode=0x1100)
    dll.BinkOpen.argtypes = [C.c_char_p, C.c_uint32]
    dll.BinkOpen.restype = C.c_void_p
    dll.BinkClose.argtypes = [C.c_void_p]
    dll.BinkClose.restype = None
    dll.BinkDoFrame.argtypes = [C.c_void_p]
    dll.BinkDoFrame.restype = C.c_int
    dll.BinkNextFrame.argtypes = [C.c_void_p]
    dll.BinkNextFrame.restype = None
    dll.BinkGetError.argtypes = []
    dll.BinkGetError.restype = C.c_char_p
    handle = dll.BinkOpen(str(path).encode(), 0)
    assert handle, dll.BinkGetError()
    try:
        frames = struct.unpack('<7I', C.string_at(handle, 28))[2]
        assert frames == expected_frames
        results = []
        for i in range(frames):
            results.append(dll.BinkDoFrame(handle))
            if i+1 < frames:
                dll.BinkNextFrame(handle)
        return {'frames': frames, 'decode_returns': results,
            'decoder_error': (dll.BinkGetError() or b'').decode(errors='replace')}
    finally:
        dll.BinkClose(handle)

def prepare():
    closed()
    guard_index()
    assert not STATE.exists(), 'Existing diagnostic state: inspect or restore before preparing again.'
    OUT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ROOT / 'outputs/Overstrike/Mods Library/NoIntro.stage') as z:
        clip = z.read('0/movies/boot/bootsequence_pc.movie')
        assert all(z.read('0/movies/boot/bootsequence_' + region + '.movie') == clip
            for region in ['pc', 'eu', 'china'])
    assert sha(clip) == CLIP_SHA256
    assert clip[:4] == b'KB2j' and struct.unpack_from('<I', clip, 4)[0]+8 == len(clip)
    rows = table()
    with (GAME / 'd/movie').open('rb') as f:
        for row in rows:
            data = read_range(f, row)
            assert data[:4] == b'KB2j' and struct.unpack_from('<I', data, 4)[0]+8 == len(data)
            assert struct.unpack_from('<I', data, 8)[0] in (547, 706)
            backup = OUT / (row['id'] + '.original.movie')
            backup.write_bytes(data)
            row['original_sha256'] = sha(data)
            row['patched_sha256'] = sha(clip + data[len(clip):])
            row['backup'] = backup.name
            assert sha(backup.read_bytes()) == row['original_sha256']
            if row['id'] == '905EBDB8C12D66E0':
                padded = OUT / 'decoder-test.bk2'
                padded.write_bytes(clip + data[len(clip):])
    (OUT / 'replacement.bk2').write_bytes(clip)
    decoder = decode_test(OUT / 'decoder-test.bk2')
    assert not decoder['decoder_error']
    (OUT / 'toc.before').write_bytes((GAME / 'toc').read_bytes())
    state = {'status': 'prepared', 'archive': str(GAME / 'd/movie'),
        'clip_sha256': sha(clip), 'clip_length': len(clip), 'rows': rows,
        'toc_sha1': CAMERA_TOC_SHA1, 'toc_bak_sha1': CLEAN_SHA1,
        'padded_clip_decoder_test': decoder, 'in_game_result': 'pending'}
    STATE.write_text(json.dumps(state, indent=2))
    print(json.dumps(state, indent=2))

def modify(restore=False):
    closed()
    guard_index()
    state = json.loads(STATE.read_text())
    expected_status = 'installed' if restore else 'prepared'
    assert state['status'] == expected_status, state['status']
    clip = (OUT / 'replacement.bk2').read_bytes()
    assert sha(clip) == CLIP_SHA256
    originals = {}
    for row in state['rows']:
        data = (OUT / row['backup']).read_bytes()
        assert sha(data) == row['original_sha256']
        originals[row['id']] = data
    # All source checks and backup checks precede the first write.
    with (GAME / 'd/movie').open('r+b') as f:
        for row in state['rows']:
            expected = row['patched_sha256'] if restore else row['original_sha256']
            assert sha(read_range(f, row)) == expected, 'Movie differs from prepared state.'
        try:
            for row in state['rows']:
                f.seek(row['offset'])
                payload = originals[row['id']][:len(clip)] if restore else clip
                assert f.write(payload) == len(payload)
            f.flush()
            os.fsync(f.fileno())
            for row in state['rows']:
                expected = row['original_sha256'] if restore else row['patched_sha256']
                assert sha(read_range(f, row)) == expected
        except BaseException:
            # Complete source backups allow recovery even after a partial write.
            for row in state['rows']:
                f.seek(row['offset'])
                f.write(originals[row['id']])
            f.flush()
            os.fsync(f.fileno())
            raise
    guard_index()
    state['status'] = 'restored' if restore else 'installed'
    state['archive_verified'] = True
    state['toc_and_backup_unchanged'] = True
    STATE.write_text(json.dumps(state, indent=2))
    print(json.dumps({'status': state['status'], 'bytes_written': 3*len(clip),
        'toc_and_backup_unchanged': True, 'archive_ranges_verified': True,
        'in_game_result': 'pending'}, indent=2))

if __name__ == '__main__':
    mode = argparse.ArgumentParser()
    mode.add_argument('action', choices=['prepare', 'install', 'restore'])
    action = mode.parse_args().action
    if action == 'prepare':
        prepare()
    else:
        modify(action == 'restore')
