import json
from pathlib import Path
out=Path('outputs/startup-repair')
p=out/'isolation-verification.json';d=json.loads(p.read_text());d['startup_test']='same configuration previously confirmed by user to reach the main menu; restored after failed short-intro test';p.write_text(json.dumps(d,indent=2))
p=out/'compatible-intro-install-verification.json';d=json.loads(p.read_text());d['compatible_intro_enabled']=False;d['current_state']='removed from active profiles and both Overstrike libraries; original movies restored';p.write_text(json.dumps(d,indent=2))
(out/'README.md').write_text('''# Startup repair result

The black screen was isolated to intro replacements. The game reached the menu with the original intro movies and the camera mod enabled. Both the original NoIntro package and a locally prepared short clip caused the black screen. Decoder validation alone did not prove compatibility with the game’s startup sequence.

The original intro movies are restored. Both Overstrike copies now have `NoIntro.stage` disabled and `PhotoMode-10x-Tether1000.stage` enabled. The failed experimental replacement was removed from their profiles and libraries. The native camera DLL is unchanged.

The restored asset index differs from the Steam original only for the Photo Mode config asset `AED6101948AAFA54`. All three boot movies and all other asset records match the original. This is the same configuration the user confirmed reaches the menu.

`toc.BAK` now matches Steam depot 1895881, manifest 2186341403927512776, build 23987138: SHA-1 `64946f571579d9ea0a17e675682e2994dc0f20fc`. `toc.steam-original` retains that verified clean index. The earlier backup had already contained modded references; replacing it alone did not fix the legacy intro mod.

`isolation-verification.json` records the stable final configuration. `compatible-intro-install-verification.json` records the failed experiment. `backup-before/` and the profile backups retain recovery files. Do not use modified recovery indices as clean Overstrike baselines.

After a future game update, verify game files before replacing Overstrike’s baseline. Never delete `toc.BAK` and reinstall while `toc` is still modded, because Overstrike would make that modified index the new backup. Keep the legacy NoIntro disabled on this build.

Relevant author reports: https://www.nexusmods.com/ratchetandclankriftapart/mods/5?tab=posts.

No LOD override has been installed yet. Its requested scope remains Photo Mode only.
''',encoding='utf-8')
print('Final startup configuration and test results recorded.')
