import json,time,resource
import numpy as np
from matchcut import store,media
from matchcut.inference import Engine
store.init();collection=store.assets();engine=Engine()
report={'device':engine.device,'version':engine.version,'assets':len(collection),'duration_seconds':sum(a['duration'] for a in collection),'index_seconds_sum':sum(a.get('index_seconds',0) for a in collection),'queries':[]}
a=collection[0];im=media.frames(a,[media.nearest(a,2.1)],max_size=224)
for _ in range(2):engine.embed(im)
for a in collection:
    eligible=[i for i,t in enumerate(a['times']) if t>=2.1]
    if not eligible:continue
    frame=eligible[0]
    try:
        base=engine.search(a,frame,collection,mode='appearance');combined=engine.search(a,frame,collection)
    except ValueError:continue
    row={'source':a['id'],'name':a['name'],'frame':frame,'appearance':base,'combined':combined}
    if combined['results']:
        c=combined['results'][0];t=time.perf_counter();preview=media.render(a,c['out_frame'],store.asset(c['asset']),c['frame']);row['preview_seconds']=time.perf_counter()-t;row['preview']=preview
    report['queries'].append(row);print(a['name'],combined['timing']['total'],row.get('preview_seconds'),flush=True)
report['workspace_bytes']=store.check_budget();report['peak_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
(store.DATA/'benchmark.json').write_text(json.dumps(report,indent=2))
# Same actual windows for classical/learned motion. First call is kept as cold.
motion=[]
for a in collection[:5]:
    i=media.nearest(a,min(2.1,a['duration']-.5))
    for method in ('farneback','raft'):
        for rep in range(2):
            t=time.perf_counter();v=engine.motion(a,i,'in',method);motion.append({'source':a['id'],'method':method,'repeat':rep,'seconds':time.perf_counter()-t,'descriptor':v.tolist()})
(store.DATA/'motion-benchmark.json').write_text(json.dumps(motion,indent=2));print('Motion comparison complete',flush=True)
