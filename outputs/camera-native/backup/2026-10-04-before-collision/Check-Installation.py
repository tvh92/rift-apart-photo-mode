"""Read-only audit of the supported camera and fixed-intro installation."""
import hashlib, json, re, struct, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart')
MANAGERS = [ROOT / 'outputs/Overstrike', Path(r'C:\Users\Tim\Documents\Bestanden\Downloads\Overstrike 1 1.8.1 2026-09-04T22-57Z vzbjnz4Zh')]
CAMERA_ID = 0xAED6101948AAFA54
EXPECTED_TOC = '64946f571579d9ea0a17e675682e2994dc0f20fc'
EXPECTED_PAYLOAD = '7e1538b0742262daec41965bdce20d4a0252502a2eded61c87d97fe56373d7c5'
INTRO_STAGE = 'NoIntro-Fixed-2Seconds.stage'
INTRO_PAYLOADS = {
    0x851735C03E050852: '36367a6086042b299ab96f0949822f131bfaaf287bfbb316f1eb4ba8677529b7',
    0x8B203B05CA2AEB50: '36367a6086042b299ab96f0949822f131bfaaf287bfbb316f1eb4ba8677529b7',
    0x905EBDB8C12D66E0: 'c5051b8e610c4e22f5df5e4ed3e04482055173dfc13da6e498aa39019b09f025'}

def digest(path, kind='sha256'):
    h = hashlib.new(kind)
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def parse(data):
    assert struct.unpack_from('<I', data, 8)[0] == 0x44415431
    count = struct.unpack_from('<H', data, 20)[0]
    sections = {tag: data[8+pos:8+pos+size] for tag, pos, size in
        (struct.unpack_from('<III', data, 24+12*i) for i in range(count))}
    ids = [x[0] for x in struct.iter_unpack('<Q', sections[0x506D7B8A])]
    rows = list(struct.iter_unpack('<IIIi', sections[0x65BCF461]))
    archive_bytes = sections[0x398ABFF0]
    archives = [archive_bytes[i:i+40].split(b'\0')[0].decode().replace('\\', '/')
        for i in range(0, len(archive_bytes), 66)]
    assert len(ids) == len(rows)
    return sections, ids, rows, archives

def audit():
    acf = Path(r'C:\Program Files (x86)\Steam\steamapps\appmanifest_1895880.acf').read_text()
    assert re.search(r'"buildid"\s+"23987138"', acf), 'Game build changed'
    assert re.search(r'"StateFlags"\s+"4"', acf), 'Steam update/verification incomplete'
    assert re.search(r'"1895881"\s*\{\s*"manifest"\s+"2186341403927512776"', acf), 'Depot manifest changed'
    assert digest(GAME/'RiftApart.exe') == '51299faca61866cf10ea9035a15b8f22600a56557dd5ffc1aad390d5a54e6d82'
    clean = (ROOT/'outputs/startup-repair/toc.steam-original').read_bytes()
    assert hashlib.sha1(clean).hexdigest() == EXPECTED_TOC
    assert digest(GAME/'toc.BAK', 'sha1') == EXPECTED_TOC, 'Bad or outdated toc.BAK'
    profiles = [json.loads((m/'Profiles/RCRA (Steam).json').read_text(encoding='utf-8-sig')) for m in MANAGERS]
    assert profiles[0]['mods'] == profiles[1]['mods'], 'Manager profiles disagree'
    camera_mod = 'PhotoMode-10x-Tether1000.stage'
    camera_only = [['NoIntro.stage', False], [camera_mod, True]]
    fixed_both = [['NoIntro.stage', False], [INTRO_STAGE, True], [camera_mod, True]]
    assert profiles[0]['mods'] in (camera_only, fixed_both), 'Unrecognized enabled mods'
    intro_enabled = profiles[0]['mods'] == fixed_both
    active_stages = [INTRO_STAGE, camera_mod] if intro_enabled else [camera_mod]
    targets = {CAMERA_ID: (camera_mod, '0/AED6101948AAFA54', EXPECTED_PAYLOAD)}
    if intro_enabled:
        targets.update({aid: (INTRO_STAGE, f'0/{aid:016X}', expected) for aid, expected in INTRO_PAYLOADS.items()})
    live = (GAME/'toc').read_bytes()
    a, ids, original, names = parse(clean)
    b, live_ids, current, live_names = parse(live)
    assert a.keys() == b.keys() and ids == live_ids
    for tag in a:
        if tag not in (0x65BCF461, 0x398ABFF0):
            assert a[tag] == b[tag], f'Unexpected section edit: {tag:08X}'
    assert b[0x398ABFF0][:len(a[0x398ABFF0])] == a[0x398ABFF0]
    assert len(live_names) == len(names)+len(active_stages), 'Unexpected archive additions'
    changed = [aid for aid, x, y in zip(ids, original, current) if x != y]
    assert set(changed) == targets.keys(), f'Unexpected changed assets: {[hex(x) for x in changed]}'
    for manager, profile in zip(MANAGERS, profiles):
        assert profile['game'] == 'RCRA' and Path(profile['path']) == GAME
        assert profile['settings']['scripts'] == {'enabled': False, 'commandline': False}
        for aid, (stage, entry, expected) in targets.items():
            i = ids.index(aid)
            size, ai, offset, header = current[i]
            assert size == original[i][0] and header == original[i][3], 'Asset size/header changed'
            number = active_stages.index(stage)
            assert ai == len(names)+number and live_names[ai] == f'd/mods/mod{number}'
            with (GAME/live_names[ai]).open('rb') as f:
                f.seek(offset)
                payload = f.read(size)
            assert hashlib.sha256(payload).hexdigest() == expected, 'Installed payload mismatch'
            with zipfile.ZipFile(manager/'Mods Library'/stage) as z:
                assert payload == z.read(entry), 'Library payload differs from installed data'
    assert digest(GAME/'hid.dll') == '97b9a29eed154973fb587e0fae965c441b9956096211523aa1f99ef1d6d03e81'
    assert digest(GAME/'d/config') == 'f659e13afe36c335d3ab54441898378164a51c2c469a1a368a51c8a005310bb3'
    movie_rows = {
        0x851735C03E050852: 'a88fd460970c87b72137a5475a65cbc3b0411b9b74b8de980755d583cc20fb7b',
        0x8B203B05CA2AEB50: 'a88fd460970c87b72137a5475a65cbc3b0411b9b74b8de980755d583cc20fb7b',
        0x905EBDB8C12D66E0: 'efaba807f3b24cf143f19da7689952fee925859de9b20b793cc7ab3507726fd7'}
    with (GAME/'d/movie').open('rb') as f:
        for aid, expected in movie_rows.items():
            length, ai, offset, _ = original[ids.index(aid)]
            assert names[ai] == 'd/movie'
            f.seek(offset)
            assert hashlib.sha256(f.read(length)).hexdigest() == expected, 'Movie bytes changed'
    return {'clean_backup_verified': True, 'steam_build': 23987138,
        'only_changed_assets': [f'{aid:016X}' for aid in changed], 'payloads_match_both_libraries': True,
        'other_index_sections_unchanged': True, 'both_profiles_match': True, 'fixed_intro_enabled': intro_enabled,
        'camera_dll_unchanged': True, 'base_config_vanilla': True,
        'all_original_boot_movies_verified': True, 'in_game_status': 'Audit checks files only; see startup test results separately.'}

if __name__ == '__main__':
    report = audit()
    (ROOT/'outputs/startup-repair/installation-audit.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
