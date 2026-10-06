import ast,struct,hashlib,json
from pathlib import Path
ns={};tree=ast.parse(Path('work/inspect_photo_config.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef))],type_ignores=[]),'helpers','exec'),ns)
paths={'original':Path('outputs/startup-repair/toc.steam-original'),'legacy_reinstalled':Path('outputs/startup-repair/backup-before/toc'),'current_camera_only':Path(r'C:\Program Files (x86)\Steam\steamapps\common\Ratchet & Clank - Rift Apart\toc')}
# Older failed index is retained before rebuilding from fresh baseline; compare separately.
base=paths['original'].read_bytes();s0=ns['sections'](base[8:]);report={}
for name,p in paths.items():
 d=p.read_bytes();s=ns['sections'](d[8:]);rows=[]
 for tag,(off,n) in s.items():
  aoff,an=s0[tag];a=base[8+aoff:8+aoff+an];b=d[8+off:8+off+n]
  rows.append({'tag':f'{tag:08X}','original_size':an,'size':n,'same':a==b,'original_sha256':hashlib.sha256(a).hexdigest(),'sha256':hashlib.sha256(b).hexdigest()})
 report[name]={'sha1':hashlib.sha1(d).hexdigest(),'sections':rows}
print(json.dumps(report,indent=2));Path('work/startup-toc-sections.json').write_text(json.dumps(report,indent=2))
x=json.loads(Path('work/overstrike-tree.json').read_text())
for row in x.get('tree',[]):
 p=row['path']
 if any(k in p for k in ['TOC_I29','ArchivesSection','ArchiveSection']):print(p)
