"""Capture real demo media for the eye close-up / Appearance baseline query.

Requires the app running at http://127.0.0.1:8765 (./scripts/run.sh).
Writes frames, preview/export MP4s and results.json to demo/part1/captures/.
"""
import argparse, json, shutil, time, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE='http://127.0.0.1:8765'
OUT=ROOT/'demo/part1/captures'

def call(path,body=None):
    data=None if body is None else json.dumps(body).encode()
    req=urllib.request.Request(BASE+path,data=data,headers={'Content-Type':'application/json'} if data else {})
    with urllib.request.urlopen(req,timeout=60) as r:return json.loads(r.read())

def fetch(path,target):
    with urllib.request.urlopen(BASE+path,timeout=120) as r:target.write_bytes(r.read())

def wait(key):
    while True:
        j=call('/api/jobs/'+key)
        if j['state']=='succeeded':return j['result']
        if j['state'] in ('failed','cancelled'):raise RuntimeError(f"Job {key} {j['state']}: {j.get('error')}")
        time.sleep(.3)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--name',default='Eye close-up')
    p.add_argument('--frame',type=int,default=50)
    p.add_argument('--mode',default='appearance')
    p.add_argument('--collection',default='targeted')
    p.add_argument('--pick',type=int,default=0,help='Result rank to render (0 = top)')
    args=p.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)

    asset=next(a for a in call('/api/assets') if a['name']==args.name)
    fetch(f"/api/frame/{asset['id']}/{args.frame}",OUT/'outgoing.jpg')

    started=time.time()
    result=wait(call('/api/search',dict(asset=asset['id'],frame=args.frame,mode=args.mode,collection=args.collection,
                                         nearby=True,refine=False,before=2,after=2))['id'])
    wall=time.time()-started
    for i,c in enumerate(result['results'],1):
        fetch(f"/api/frame/{c['asset']}/{c['frame']}",OUT/f'candidate-{i:02d}.jpg')
        if c['out_frame']!=args.frame:fetch(f"/api/frame/{asset['id']}/{c['out_frame']}",OUT/f'candidate-{i:02d}-outgoing.jpg')

    chosen=result['results'][args.pick]
    edit=dict(a=asset['id'],ai=chosen['out_frame'],b=chosen['asset'],bi=chosen['frame'],framing='pad',before=2,after=2)
    renders={}
    for label,height in (('preview',360),('export-1080p',1080)):
        r=wait(call('/api/render',dict(edit,height=height))['id'])
        shutil.copyfile(ROOT/'data'/r['url'].lstrip('/'),OUT/f'{label}.mp4')
        renders[label]=dict(file=f'{label}.mp4',source_url=r['url'],spec=r['spec'])

    summary=dict(query=dict(name=asset['name'],asset=asset['id'],frame=args.frame,time=asset['times'][args.frame],
                            pts=asset['pts'][args.frame],mode=args.mode,collection=args.collection),
                 timing=result.get('timing'),wall_seconds=wall,device=result.get('device'),version=result.get('version'),
                 ranking_version=result.get('ranking_version'),
                 results=[{k:c.get(k) for k in ('name','score','appearance','composition','motion','pose','shape','time','out_time','frame','out_frame')}
                          for c in result['results']],
                 rendered=dict(rank=args.pick+1,name=chosen['name'],edit=edit,**renders))
    (OUT/'results.json').write_text(json.dumps(summary,indent=2))
    print(f"{len(result['results'])} matches in {result['timing']['total']:.2f}s; rendered #{args.pick+1} {chosen['name']} -> {OUT}")
    for i,c in enumerate(result['results'],1):print(f"  {i}. {c['name']:<22} score {c['score']:.3f}  appearance {c['appearance']:.3f}")

if __name__=='__main__':main()
