import numpy as np
from matchcut.inference import motion_similarity

def test_ordered_motion_stationary_and_speed():
    right=np.ones(8)*.1
    assert motion_similarity(right,right)>.99
    assert motion_similarity(right,-right)==0
    assert motion_similarity(right,right*4)<.3
    assert motion_similarity(np.zeros(8),np.zeros(8))==1
    assert motion_similarity(right,np.zeros(8))==0

def test_source_family_diversity_and_cache(tmp_path,monkeypatch):
    from matchcut import inference,media
    e=inference.Engine.__new__(inference.Engine);e.version='test';e.device='cpu'
    a=dict(id='a',name='Fixture',family='same',times=[i/10 for i in range(50)],duration=5,cuts=[0,50])
    others=[dict(a,id='same-excerpt'),dict(a,id='b',family='b'),dict(a,id='c',family='c')]
    monkeypatch.setattr(media,'frames',lambda a,i,**kw:[None for _ in i])
    monkeypatch.setattr(inference.shapes,'describe',lambda im:np.full((3,4),np.nan))
    e.load_shapes=lambda a,ids:np.full((len(ids),3,4),np.nan)
    e.embed=lambda images:(np.array([[1.,0.]]*len(images)),np.array([[1.,0.]]*len(images)))
    e.motion=lambda *args:np.ones(8)*.1
    e.observations=lambda a,ids,side:([None for _ in ids],[np.ones(8)*.1 for _ in ids])
    from types import SimpleNamespace
    e.pose=SimpleNamespace(infer=lambda im:np.full((12,3),np.nan))
    existing=tmp_path/'exists';existing.touch();e.feature_path=lambda a:existing
    e.load=lambda a:dict(ids=np.array([0,5]),global_=np.array([[.8,.6],[.7,.7]]),spatial=np.array([[.7,.7],[.8,.6]]),motion=np.ones((2,8))*.1,pose=np.full((2,12,3),np.nan))
    r=e.search(a,25,others,nearby=False,refine=False)
    assert {c['asset'] for c in r['results']}=={'b','c'}
    assert all(c['out_frame']==25 for c in r['results'])

def test_refinement_uses_valid_frames_and_never_discards_seed(monkeypatch,tmp_path):
    from matchcut import inference,media
    from types import SimpleNamespace
    e=inference.Engine.__new__(inference.Engine);e.version='test';e.device='cpu'
    a=dict(id='a',name='out',family='a',times=[i/100 for i in range(500)],duration=5,cuts=[0,500])
    b=dict(a,id='b',name='in',family='b')
    monkeypatch.setattr(media,'frames',lambda a,i,**kw:[None for _ in i])
    monkeypatch.setattr(inference.shapes,'describe',lambda im:np.full((3,4),np.nan))
    e.embed=lambda im:(np.array([[1.,0.]]),np.array([[1.,0.]]))
    e.pose=SimpleNamespace(infer=lambda im:np.full((12,3),np.nan))
    e.motion=lambda *args:np.ones(8)*.1
    e.observations=lambda a,ids,side:([None for _ in ids],[np.ones(8)*.1 for _ in ids])
    path=tmp_path/'feature';path.touch();e.feature_path=lambda a:path
    e.load=lambda a:dict(ids=np.array([100]),global_=np.array([[.6,.8]]),spatial=np.array([[.6,.8]]),motion=np.ones((1,8))*.1,pose=np.full((1,12,3),np.nan))
    e.load_shapes=lambda a,ids:np.full((len(ids),3,4),np.nan)
    seen=[]
    def detail(asset,ids):
        seen.extend(ids)
        return [(np.array([.9,.43]),np.array([.9,.43]),np.ones(8)*.1,np.full((12,3),np.nan),np.full((3,4),np.nan)) for _ in ids]
    e.detail=detail
    coarse=e.search(a,250,[b],nearby=False,refine=False)
    fine=e.search(a,250,[b],nearby=False,refine=True)
    assert fine['results'][0]['score']>=coarse['results'][0]['score']
    assert fine['results'][0]['out_frame']==250
    assert any(i%50 for i in seen)
    assert all(media.window(b,i,'in') for i in seen)
    short=e.search(a,60,[b],nearby=False,refine=False,before=.5,after=.5)
    assert short['before']==short['after']==.5
    assert short['results'][0]['out_frame']==60
