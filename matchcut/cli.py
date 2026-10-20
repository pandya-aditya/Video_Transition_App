import argparse, json, time
from . import store,media
from .inference import Engine

def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['samples','search','motion-benchmark','import-folder']);p.add_argument('--folder');p.add_argument('--collection',default='targeted');p.add_argument('--asset');p.add_argument('--frame',type=int);args=p.parse_args()
    store.init();engine=Engine()
    if args.command=='import-folder':
        from .library import import_folder
        if not args.folder:p.error('--folder is required')
        print(import_folder(args.folder,args.collection,engine,lambda p:print(f'{p:.0%}',flush=True)))
    elif args.command=='samples':
        for source in json.loads((store.ROOT/'samples-manifest.json').read_text()):
            a=media.import_file(store.ROOT/source['path'],source.get('name',source['title'].removeprefix('File:')),source['family'],source)
            a.update(family=source['family'],name=source.get('name',a['name']),attribution=source);store.save_asset(a)
            engine.index(a);print(a['name'],a['duration'],a.get('index_seconds'),flush=True)
    elif args.command=='search':
        a=store.asset(args.asset) if args.asset else store.assets()[0]
        frame=args.frame if args.frame is not None else media.nearest(a,2.1)
        result=engine.search(a,frame,store.assets())
        for c in result['results']:
            t=time.perf_counter(); c['preview']=media.render(a,c['out_frame'],store.asset(c['asset']),c['frame']);c['render_seconds']=time.perf_counter()-t
        (store.DATA/'experiment.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result,indent=2))
    else:
        rows=[]
        for a in store.assets():
            i=media.nearest(a,a['duration']/2)
            for method in ('farneback','raft'):
                for repeat in range(3):
                    t=time.perf_counter();v=engine.motion(a,i,'in',method);elapsed=time.perf_counter()-t
                    rows.append(dict(asset=a['id'],method=method,repeat=repeat,seconds=elapsed,flow=v.tolist()))
        (store.DATA/'motion-benchmark.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
