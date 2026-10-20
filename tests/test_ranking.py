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
    e.embed=lambda images:(np.array([[1.,0.]]*len(images)),np.array([[1.,0.]]*len(images)))
    e.motion=lambda *args:np.ones(8)*.1
    from types import SimpleNamespace
    e.pose=SimpleNamespace(infer=lambda im:np.full((12,3),np.nan))
    existing=tmp_path/'exists';existing.touch();e.feature_path=lambda a:existing
    e.load=lambda a:dict(ids=np.array([0,5]),global_=np.array([[.8,.6],[.7,.7]]),spatial=np.array([[.7,.7],[.8,.6]]),motion=np.ones((2,8))*.1,pose=np.full((2,12,3),np.nan))
    r=e.search(a,25,others,nearby=False)
    assert {c['asset'] for c in r['results']}=={'b','c'}
    assert all(c['out_frame']==25 for c in r['results'])
