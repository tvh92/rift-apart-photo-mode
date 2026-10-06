import json
from pathlib import Path
p=Path('outputs/startup-repair/compatible-intro-install-verification.json');d=json.loads(p.read_text());d['in_game_test']='failed: user reported persistent black screen';d['compatible_intro_enabled']=False;d['current_state']='pending restoration of original intro movies';p.write_text(json.dumps(d,indent=2))
p=Path('outputs/startup-repair/isolation-verification.json');d=json.loads(p.read_text());d['startup_test']='passed: user confirmed the main menu loads with original intro movies and camera mod enabled';p.write_text(json.dumps(d,indent=2))
