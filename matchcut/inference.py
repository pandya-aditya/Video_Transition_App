import json, os, time
import numpy as np
import torch
import torch.nn.functional as F
import cv2
from PIL import ImageOps
from .store import DATA, ROOT, ident, save_asset
from . import media, pose

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

    def feature_path(self,a):return DATA/'features'/f"{a['id']}-{self.version}.npz"

    def index(self,a,progress=lambda p:None):
        path=self.feature_path(a)
        if path.exists():return self.load(a)
        start=time.perf_counter()
        ids=sorted(set(media.nearest(a,t) for t in np.arange(0,a['duration'],.5)))
        glob,spatial,flow,poses=[],[],[],[]
        for offset in range(0,len(ids),8):
            batch=ids[offset:offset+8]; ims=media.frames(a,batch,max_size=224)
            g,s=self.embed(ims);glob.extend(g);spatial.extend(s)
            poses.extend(self.pose.infer(im) for im in ims)
            for i in batch:flow.append(self.motion(a,i,'in'))
            progress(min(.98,(offset+len(batch))/len(ids)))
        temp=path.with_suffix('.partial.npz')
        np.savez_compressed(temp,ids=ids,global_=glob,spatial=spatial,motion=flow,pose=poses)
        temp.replace(path)
        a.update(status='ready',version=self.version,index_seconds=time.perf_counter()-start,device=self.device)
        save_asset(a)
        return self.load(a)

    def load(self,a):
        key=(a['id'],self.version)
        if key not in self.cache:
            with np.load(self.feature_path(a)) as f:self.cache[key]={k:f[k] for k in f.files}
        return self.cache[key]

    def search(self,a,frame,collection,mode='combined',nearby=True):
        start=time.perf_counter(); media.window(a,frame,'out')
        query_ids=[frame]
        if nearby:
            for dt in (-.5,-.25,.25,.5):
                i=media.nearest(a,a['times'][frame]+dt)
                try: media.window(a,i,'out'); query_ids.append(i)
                except ValueError: pass
        query_ids=list(dict.fromkeys(query_ids)); query_images=media.frames(a,query_ids,max_size=224)
        qg,qs=self.embed(query_images); qp=[self.pose.infer(im) for im in query_images]
        qm=[self.motion(a,i,'out') for i in query_ids]
        retrieval_done=time.perf_counter(); candidates=[]
        for b in collection:
            if b['family']==a['family'] or b['id']==a['id'] or not self.feature_path(b).exists():continue
            features=self.load(b)
            for qi,ai in enumerate(query_ids):
                appearance=features['global_']@qg[qi]; composition=features['spatial']@qs[qi]
                # Union of global and spatial neighbors improves recall over global-only.
                shortlist=set(np.argsort(appearance)[-24:])
                if mode!='appearance':shortlist.update(np.argsort(composition)[-24:])
                for k in shortlist:
                    bi=int(features['ids'][k])
                    try:media.window(b,bi,'in')
                    except ValueError:continue
                    ap=float(appearance[k]); comp=float(composition[k])
                    # Almost identical frames: duplicate guard, not a semantic exclusion.
                    if ap>.985 and comp>.985:continue
                    motion=motion_similarity(qm[qi],features['motion'][k])
                    ps=pose.similarity(qp[qi],features['pose'][k])
                    combined=.35*ap+.4*comp+.25*motion
                    score=ap if mode=='appearance' else (combined if ps is None else .7*combined+.3*ps)
                    candidates.append(dict(asset=b['id'],frame=bi,out_frame=ai,score=score,
                        appearance=ap,composition=comp,motion=motion,pose=ps,
                        time=b['times'][bi],out_time=a['times'][ai],name=b['name'],family=b['family']))
        candidates.sort(key=lambda c:c['score'],reverse=True)
        chosen=[]; families=set()
        for c in candidates:
            if c['family'] in families:continue
            chosen.append(c);families.add(c['family'])
            if len(chosen)==6:break
        return dict(source=a['id'],selected_frame=frame,results=chosen,mode=mode,version=self.version,
                    device=self.device,timing=dict(query_features=retrieval_done-start,
                    retrieval_ranking=time.perf_counter()-retrieval_done,total=time.perf_counter()-start),
                    eligible_candidates=len(candidates),note='Heuristic scores, not probabilities. Pose agreement is shown only when enough visible joints are detected.')
