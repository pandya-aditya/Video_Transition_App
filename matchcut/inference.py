import json, os, time
import numpy as np
import torch
import torch.nn.functional as F
import cv2
from PIL import ImageOps
from .store import DATA, ROOT, ident, save_asset
from . import media, pose, shapes

os.environ['HF_HUB_OFFLINE']='1'
os.environ['TORCH_HOME']=str(DATA/'models/torch')
torch.set_num_threads(4)

def unit(x):
    return x / np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1e-8)

def motion_similarity(a,b):
    an,bn=np.linalg.norm(a),np.linalg.norm(b)
    if max(an,bn)<.003: return 1.
    if min(an,bn)<.003: return 0.
    direction=float(np.dot(a,b)/(an*bn))
    speed=np.exp(-abs(np.log((an+1e-6)/(bn+1e-6))))
    return float(max(0,direction)*speed)

class Engine:
    def __init__(self, device=None, adapter=None):
        from transformers import AutoModel, AutoImageProcessor
        self.device=device or ('mps' if torch.backends.mps.is_available() else 'cpu')
        path=DATA/'models/dinov2-small'
        self.processor=AutoImageProcessor.from_pretrained(path,local_files_only=True)
        self.model=AutoModel.from_pretrained(path,local_files_only=True).eval()
        # Interpolate the fixed 224px positional grid once on CPU. Torch 2.5 MPS
        # lacks bicubic interpolation; all transformer inference stays on MPS.
        with torch.no_grad():
            pos=self.model.embeddings.interpolate_pos_encoding(torch.zeros(1,257,384),224,224)
        self.model.embeddings.position_embeddings=torch.nn.Parameter(pos,requires_grad=False)
        self.model.to(self.device)
        self.adapter=adapter
        if adapter: self.model.load_state_dict(torch.load(adapter,weights_only=True,map_location=self.device),strict=False)
        lock=json.loads((ROOT/'models.lock.json').read_text())
        self.config=dict(model=lock,preprocess='decode224-pad224-imagenet-v2',spatial='2x2-patch-pool',sample_seconds=.5,
                         motion='farneback-224x128-0.12s-grid2-v1',adapter=str(adapter))
        if adapter:
            import hashlib
            self.config['adapter']=hashlib.sha256(open(adapter,'rb').read()).hexdigest()
        self.config['pose']='blazepose-lite-v1-pad256-visible06'
        self.version=ident(self.config); self.raft=None; self.cache={}
        self.pose=pose.Pose()
        self.detail_cache={};self.shape_cache={}

    def tensor(self,images):
        # Preserve the entire composition; explicitly override center crop.
        images=[ImageOps.pad(im,(224,224),color=(0,0,0)) for im in images]
        return self.processor(images=images,do_resize=False,do_center_crop=False,return_tensors='pt')['pixel_values'].to(self.device)

    def features_tensor(self,x):
        h=self.model(pixel_values=x).last_hidden_state
        global_=F.normalize(h[:,0],dim=-1)
        patches=h[:,1:].reshape(-1,16,16,384).permute(0,3,1,2)
        spatial=F.normalize(F.adaptive_avg_pool2d(patches,(2,2)).flatten(1),dim=-1)
        return global_,spatial

    def embed(self,images):
        with torch.inference_mode():
            g,s=self.features_tensor(self.tensor(images))
            return g.cpu().numpy(),s.cpu().numpy()

    def flow(self,first,second,dt,method='farneback'):
        size=(224,128)
        a=np.asarray(first.resize(size)); b=np.asarray(second.resize(size))
        if method=='raft':
            from torchvision.models.optical_flow import raft_small
            if self.raft is None:
                # Do not permit implicit network requests in the worker.
                path=DATA/'models/torch/hub/checkpoints/raft_small_C_T_V2-01064c6d.pth'
                self.raft=raft_small(weights=None).to(self.device).eval()
                self.raft.load_state_dict(torch.load(path,weights_only=True,map_location=self.device))
            x=torch.from_numpy(a.copy()).permute(2,0,1)[None].to(self.device).float()/127.5-1
            y=torch.from_numpy(b.copy()).permute(2,0,1)[None].to(self.device).float()/127.5-1
            with torch.inference_mode(): field=self.raft(x,y,num_flow_updates=12)[-1][0].permute(1,2,0).cpu().numpy()
        else:
            field=cv2.calcOpticalFlowFarneback(cv2.cvtColor(a,cv2.COLOR_RGB2GRAY),cv2.cvtColor(b,cv2.COLOR_RGB2GRAY),None,.5,3,15,3,5,1.2,0)
        field=field/np.array([size[0],size[1]])/max(dt,1e-6)
        # Mean vector per quadrant retains rotation that a global mean can cancel.
        return np.array([field[y:y+64,x:x+112].mean(axis=(0,1)) for y in (0,64) for x in (0,112)]).flatten().astype('float32')

    def motion(self,a,i,side,method='farneback'):
        t=a['times']; lo,hi=media.shot_bounds(a,i)
        j=media.nearest(a,t[i]+(.12 if side=='in' else -.12))
        j=max(lo,min(hi-1,j)); p,q=sorted((i,j))
        if p==q:return np.zeros(8,dtype='float32')
        images=media.frames(a,[p,q],max_size=224)
        return self.flow(*images,t[q]-t[p],method)

    def observations(self,a,ids,side):
        """Decode shared visual/flow frames once per batch, not once per candidate."""
        pairs=[]
        for i in ids:
            lo,hi=media.shot_bounds(a,i)
            j=max(lo,min(hi-1,media.nearest(a,a['times'][i]+(.12 if side=='in' else -.12))))
            pairs.append(tuple(sorted((i,j))))
        wanted=sorted(set(ids)|{i for pair in pairs for i in pair})
        decoded=dict(zip(wanted,media.frames(a,wanted,max_size=224)))
        motion=[self.flow(decoded[p],decoded[q],a['times'][q]-a['times'][p]) if p!=q else np.zeros(8,dtype='float32') for p,q in pairs]
        return [decoded[i] for i in ids],motion

    def feature_path(self,a):return DATA/'features'/f"{a['id']}-{self.version}.npz"

    def index(self,a,progress=lambda p:None):
        path=self.feature_path(a)
        if path.exists():
            self.index_shapes(a,self.load(a)['ids'],progress)
            a.update(status='ready',version=self.version,device=self.device);save_asset(a)
            return self.load(a)
        start=time.perf_counter()
        ids=sorted(set(media.nearest(a,t) for t in np.arange(0,a['duration'],.5)))
        glob,spatial,flow,poses=[],[],[],[]
        for offset in range(0,len(ids),8):
            batch=ids[offset:offset+8]; ims,motions=self.observations(a,batch,'in')
            g,s=self.embed(ims);glob.extend(g);spatial.extend(s)
            poses.extend(self.pose.infer(im) for im in ims)
            flow.extend(motions)
            progress(min(.98,(offset+len(batch))/len(ids)))
        temp=path.with_suffix('.partial.npz')
        np.savez_compressed(temp,ids=ids,global_=glob,spatial=spatial,motion=flow,pose=poses)
        temp.replace(path)
        self.index_shapes(a,ids,progress)
        a.update(status='ready',version=self.version,index_seconds=time.perf_counter()-start,device=self.device)
        save_asset(a)
        return self.load(a)

    def load(self,a):
        key=(a['id'],self.version)
        if key not in self.cache:
            with np.load(self.feature_path(a)) as f:self.cache[key]={k:f[k] for k in f.files}
        return self.cache[key]

    def shape_path(self,a):
        return DATA/'features'/f"{a['id']}-{self.version}-{shapes.VERSION}.npz"

    def index_shapes(self,a,ids,progress=lambda p:None):
        path=self.shape_path(a)
        if path.exists():return
        rows=[]
        for offset in range(0,len(ids),16):
            ims=media.frames(a,ids[offset:offset+16],max_size=224)
            rows.extend(shapes.describe(im) for im in ims)
            progress(.98)
        temporary=path.with_suffix('.partial.npz')
        np.savez_compressed(temporary,ids=ids,shape=rows);temporary.replace(path)

    def load_shapes(self,a,ids):
        key=(a['id'],self.version,shapes.VERSION)
        if key not in self.shape_cache:
            path=self.shape_path(a)
            if not path.exists():return np.full((len(ids),3,4),np.nan)
            with np.load(path) as f:
                if not np.array_equal(ids,f['ids']):raise ValueError('Shape cache does not match sampled source frames')
                self.shape_cache[key]=f['shape'].copy()
        return self.shape_cache[key]

    def detail(self,a,ids):
        missing=[i for i in ids if (a['id'],self.version,i) not in self.detail_cache]
        for start in range(0,len(missing),8):
            batch=missing[start:start+8];images,motions=self.observations(a,batch,'in')
            g,s=self.embed(images)
            for j,(i,im) in enumerate(zip(batch,images)):
                self.detail_cache[(a['id'],self.version,i)]=(g[j],s[j],motions[j],self.pose.infer(im),shapes.describe(im))
        rows=[self.detail_cache[(a['id'],self.version,i)] for i in ids]
        if len(self.detail_cache)>2048:self.detail_cache.clear()
        return rows

    @staticmethod
    def candidate(a,ai,b,bi,qg,qs,qm,qp,qshape,g,s,m,p,shape,mode):
        ap=float(g@qg);comp=float(s@qs)
        if ap>.985 and comp>.985:return None
        motion=motion_similarity(qm,m);ps=pose.similarity(qp,p);ss=shapes.similarity(qshape,shape)
        combined=.35*ap+.4*comp+.25*motion
        if ps is not None:combined=.7*combined+.3*ps
        score=ap if mode=='appearance' else combined
        if mode=='shape' and np.isfinite(qshape).any():score=.55*combined+.45*(ss if ss is not None else 0.)
        return dict(asset=b['id'],frame=int(bi),out_frame=int(ai),score=score,
            appearance=ap,composition=comp,motion=motion,pose=ps,shape=ss,
            time=b['times'][bi],out_time=a['times'][ai],name=b['name'],family=b['family'])

    def search(self,a,frame,collection,mode='combined',nearby=True,refine=True,before=2.,after=2.):
        if mode not in ('appearance','combined','shape'):raise ValueError('Unknown ranking method')
        start=time.perf_counter(); media.window(a,frame,'out',before)
        query_ids=[frame]
        if nearby:
            for dt in (-.5,-.25,.25,.5):
                i=media.nearest(a,a['times'][frame]+dt)
                try: media.window(a,i,'out',before); query_ids.append(i)
                except ValueError: pass
        query_ids=list(dict.fromkeys(query_ids)); query_images,qm=self.observations(a,query_ids,'out')
        qg,qs=self.embed(query_images); qp=[self.pose.infer(im) for im in query_images]
        qshape=[shapes.describe(im) for im in query_images]
        retrieval_done=time.perf_counter(); candidates=[]
        eligible={b['id']:b for b in collection if b['family']!=a['family'] and b['id']!=a['id'] and self.feature_path(b).exists()}
        for b in eligible.values():
            features=self.load(b);shape_rows=self.load_shapes(b,features['ids'])
            for qi,ai in enumerate(query_ids):
                appearance=features['global_']@qg[qi]; composition=features['spatial']@qs[qi]
                shortlist=set(np.argsort(appearance)[-24:])
                if mode!='appearance':shortlist.update(np.argsort(composition)[-24:])
                if mode=='shape':
                    geometric=[shapes.similarity(qshape[qi],row) for row in shape_rows]
                    shortlist.update(sorted((k for k,v in enumerate(geometric) if v is not None),key=lambda k:geometric[k],reverse=True)[:24])
                for k in shortlist:
                    bi=int(features['ids'][k])
                    try:media.window(b,bi,'in',after)
                    except ValueError:continue
                    c=self.candidate(a,ai,b,bi,qg[qi],qs[qi],qm[qi],qp[qi],qshape[qi],features['global_'][k],features['spatial'][k],features['motion'][k],features['pose'][k],shape_rows[k],mode)
                    if c:candidates.append(c)
        candidates.sort(key=lambda c:c['score'],reverse=True)
        coarse_count=len(candidates);coarse_done=time.perf_counter();refined_count=0
        if refine and mode!='appearance':
            seeds=[];families=set()
            for c in candidates:
                if c['family'] in families:continue
                seeds.append(c);families.add(c['family'])
                if len(seeds)==6:break
            for seed in seeds:
                b=eligible[seed['asset']];qi=query_ids.index(seed['out_frame'])
                lo,hi=media.shot_bounds(b,seed['frame']);ids=[]
                for dt in (-.375,-.25,-.125,0,.125,.25,.375):
                    bi=media.nearest(b,seed['time']+dt)
                    if not lo<=bi<hi:continue
                    try:media.window(b,bi,'in',after);ids.append(bi)
                    except ValueError:pass
                ids=sorted(set(ids))
                for bi,feature in zip(ids,self.detail(b,ids)):
                    c=self.candidate(a,seed['out_frame'],b,bi,qg[qi],qs[qi],qm[qi],qp[qi],qshape[qi],*feature,mode)
                    if c:c['refined']=True;candidates.append(c);refined_count+=1
            candidates.sort(key=lambda c:c['score'],reverse=True)
        chosen=[];families=set()
        for c in candidates:
            if c['family'] in families:continue
            chosen.append(c);families.add(c['family'])
            if len(chosen)==6:break
        end=time.perf_counter()
        return dict(source=a['id'],selected_frame=frame,results=chosen,mode=mode,version=self.version,
            before=before,after=after,ranking_version='shape-union-refine-v2',shape_version=shapes.VERSION,device=self.device,
            timing=dict(query_features=retrieval_done-start,retrieval_ranking=coarse_done-retrieval_done,refinement=end-coarse_done,total=end-start),
            eligible_candidates=coarse_count,refined_candidates=refined_count,
            note='Heuristic scores, not probabilities. Shape uses detected circle position/size; unavailable evidence is omitted. Fine search tests incoming frames at ~0.125s intervals; manual frame stepping remains exact.')
