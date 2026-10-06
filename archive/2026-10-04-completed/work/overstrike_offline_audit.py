"""Prepare/audit isolated Overstrike installs; never target the real game."""
import ast, hashlib, json, shutil, struct, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'work/overstrike-audit/offline'
LIB = ROOT/'outputs/Overstrike/Mods Library'
ORIGINAL = ROOT/'outputs/startup-repair/toc.steam-original'
CASES = {'empty': [], 'camera': ['PhotoMode-10x-Tether1000.stage'],
    'nointro': ['NoIntro.stage'], 'both': ['NoIntro.stage', 'PhotoMode-10x-Tether1000.stage'],
    'reversed': ['PhotoMode-10x-Tether1000.stage', 'NoIntro.stage']}

def sha(data): return hashlib.sha1(data).hexdigest()

def parse(data):
    assert struct.unpack_from('<I', data, 8)[0] == 0x44415431
    count = struct.unpack_from('<H', data, 20)[0]
    sections = {tag: data[8+pos:8+pos+size] for tag, pos, size in
        (struct.unpack_from('<III', data, 24+12*i) for i in range(count))}
    ids = [x[0] for x in struct.iter_unpack('<Q', sections[0x506D7B8A])]
    rows = list(struct.iter_unpack('<IIIi', sections[0x65BCF461]))
    arc = sections[0x398ABFF0]
    names = [arc[i:i+40].split(b'\0')[0].decode().replace('\\', '/') for i in range(0, len(arc), 66)]
    return sections, ids, rows, names

def prepare():
    assert sha(ORIGINAL.read_bytes()) == '64946f571579d9ea0a17e675682e2994dc0f20fc'
    for name, mods in CASES.items():
        folder = OUT/name
        assert not folder.exists(), f'Case already exists: {folder}'
        game = folder/'test-game'
        game.mkdir(parents=True)
        shutil.copy2(ORIGINAL, game/'toc')
        profiles = folder/'Profiles'
        profiles.mkdir()
        library = folder/'Mods Library'
        library.mkdir()
        for mod in mods:
            shutil.copy2(LIB/mod, library/mod)
        profile = {'game': 'RCRA', 'path': str(game), 'mods': [[m, True] for m in mods],
            'settings': {'suit': {'language': 'us', 'allow_cross_character_suit_models': False},
                'scripts': {'enabled': False, 'commandline': False}},
            'suits': {'delete': [], 'order': [], 'modify': {}}}
        (profiles/'Audit.json').write_text(json.dumps(profile, indent=2))
    print('Prepared five isolated test profiles. All target workspace copies of toc.')

def audit():
    clean = ORIGINAL.read_bytes()
    a, ids, rows, names = parse(clean)
    reports = {}
    expected_payloads = {
        0xAED6101948AAFA54: ('PhotoMode-10x-Tether1000.stage', '0/AED6101948AAFA54'),
        0x851735C03E050852: ('NoIntro.stage', '0/movies/boot/bootsequence_china.movie'),
        0x8B203B05CA2AEB50: ('NoIntro.stage', '0/movies/boot/bootsequence_eu.movie'),
        0x905EBDB8C12D66E0: ('NoIntro.stage', '0/movies/boot/bootsequence_pc.movie')}
    for name, mods in CASES.items():
        game = OUT/name/'test-game'
        live = (game/'toc').read_bytes()
        assert (game/'toc.BAK').read_bytes() == clean, f'{name}: backup corrupted'
        b, live_ids, current, live_names = parse(live)
        assert a.keys() == b.keys() and ids == live_ids
        changed = [aid for aid, x, y in zip(ids, rows, current) if x != y]
        expected = [aid for aid, (stage, _) in expected_payloads.items() if stage in mods]
        assert set(changed) == set(expected), (name, changed, expected)
        for tag in a:
            if tag not in (0x65BCF461, 0x398ABFF0):
                assert a[tag] == b[tag], f'{name}: unrelated section edit {tag:08X}'
        assert b[0x398ABFF0][:len(a[0x398ABFF0])] == a[0x398ABFF0]
        assert len(live_names) == len(names)+len(mods)
        payloads = []
        for aid in expected:
            index = ids.index(aid)
            size, ai, offset, header = current[index]
            assert header == rows[index][3], f'{name}: header changed'
            with (game/live_names[ai]).open('rb') as f:
                f.seek(offset)
                payload = f.read(size)
            stage, entry = expected_payloads[aid]
            with zipfile.ZipFile(LIB/stage) as z:
                assert payload == z.read(entry)
            payloads.append({'asset': f'{aid:016X}', 'archive': live_names[ai],
                'offset': offset, 'bytes': size, 'header': header})
        reports[name] = {'backup_matches_steam_original': True,
            'toc_identical_to_original': live == clean, 'toc_sha1': sha(live),
            'only_expected_asset_records_changed': True, 'other_sections_unchanged': True,
            'payloads_byte_exact': payloads}
    (ROOT/'work/overstrike-audit/offline-results.json').write_text(json.dumps(reports, indent=2))
    print(json.dumps(reports, indent=2))

if __name__ == '__main__':
    {'prepare': prepare, 'audit': audit}[sys.argv[1]]()
