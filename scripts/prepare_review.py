"""Create real, blinded comparisons before training. No labels are generated."""
import json,random,time
from matchcut import store,media
from matchcut.inference import Engine
store.init();engine=Engine();rng=random.Random(17)
collection=[a for a in store.assets() if a['status']=='ready']
families=sorted({a['family'] for a in collection});rng.shuffle(families)
if len(families)<9:raise SystemExit('Need 9 independent source families for train/validation/test review; add footage first.')
path=store.DATA/'evaluation-splits.json'
split=json.loads(path.read_text()) if path.exists() else {f:('train','train','train','validation','validation','validation','test','test','test')[i%9] for i,f in enumerate(families)}
path.write_text(json.dumps(split,indent=2))
rows=[]
for a in collection:
    pool=[b for b in collection if split[b['family']]==split[a['family']]]
    for seconds in (2.1,3.1,4.1):
        if seconds>=a['duration']:continue
        ai=media.nearest(a,seconds)
        try:
            combined=engine.search(a,ai,pool,nearby=False)['results'];baseline=engine.search(a,ai,pool,mode='appearance',nearby=False)['results']
        except ValueError:continue
        if not combined or not baseline:continue
        choices=[('combined',combined[0]),('appearance',baseline[0])]
        rng.shuffle(choices);row=dict(id=store.ident([a['id'],ai]),split=split[a['family']],edit={'a':a['id'],'ai':ai},version=engine.version)
        for side,(method,c) in zip(('left','right'),choices):
            e=dict(a=a['id'],ai=ai,b=c['asset'],bi=c['frame'],height=360,framing='pad',before=2,after=2)
            row[side]=e;row[side+'_method']=method
            row[side+'_url']=media.render(a,ai,store.asset(c['asset']),c['frame'])['url']
        rows.append(row)
        print('Prepared',len(rows),a['name'],flush=True)
(store.DATA/'review-study.json').write_text(json.dumps(rows,indent=2))
