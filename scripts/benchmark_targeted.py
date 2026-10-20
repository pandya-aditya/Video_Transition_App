"""Measured collection-scoped comparisons; no taste labels or fabricated matches."""
import json,time
from matchcut import store,media
from matchcut.library import select_collection
from matchcut.inference import Engine
from PIL import Image,ImageDraw,ImageOps
store.init();e=Engine();clips=select_collection(store.assets(),'targeted')
for a in clips:e.index(a)
rows=[]
for a in clips:
    i=media.nearest(a,2.1)
    base=e.search(a,i,clips,mode='combined',nearby=False,refine=False)
    shape=e.search(a,i,clips,mode='shape',nearby=False,refine=False)
    refined=e.search(a,i,clips,mode='shape',nearby=False,refine=True)
    t=time.perf_counter();repeat=e.search(a,i,clips,mode='shape',nearby=False,refine=True)
    row=dict(source=a['id'],name=a['name'],frame=i,baseline=base,shape=shape,refined=refined,cached_seconds=time.perf_counter()-t)
    if refined['results']:
        c=refined['results'][0];t=time.perf_counter();row['preview']=media.render(a,c['out_frame'],store.asset(c['asset']),c['frame']);row['preview_seconds']=time.perf_counter()-t
    rows.append(row)
    print(a['name'],[(c['name'],round(c['score'],2),c['time']) for c in refined['results'][:2]],round(refined['timing']['total'],2),flush=True)
report=dict(assets=len(clips),duration=sum(a['duration'] for a in clips),queries=rows,workspace_bytes=store.check_budget())
(store.DATA/'targeted-benchmark.json').write_text(json.dumps(report,indent=2))
sheet=Image.new('RGB',(960,225*len(rows)),'#11120f');draw=ImageDraw.Draw(sheet)
for j,row in enumerate(rows):
    if not row['refined']['results']:continue
    c=row['refined']['results'][0]
    for k,(key,idx) in enumerate([(row['source'],c['out_frame']),(c['asset'],c['frame'])]):
        sheet.paste(ImageOps.pad(media.frames(store.asset(key),[idx])[0],(480,200)),(k*480,j*225))
    draw.text((8,j*225+204),row['name']+' -> '+c['name'],fill='white')
sheet.save(store.DATA/'targeted-results.jpg')
