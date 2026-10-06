import json
x=json.load(open('work/rivet-tree.json'))
for o in x.get('tree',[]):
 p=o['path']
 if any(k in p.lower() for k in ['photomode','perfspec','lodscale','lodclamp']):print(p)
