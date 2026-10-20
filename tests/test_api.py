from fastapi.testclient import TestClient
from matchcut import store
from matchcut.api import app

def test_origin_validation_and_durable_queue(tmp_path,monkeypatch):
    monkeypatch.setattr(store,'DATA',tmp_path);store.init()
    client=TestClient(app)
    assert client.post('/api/search',json={'asset':'x','frame':3},headers={'Origin':'https://foreign.example'}).status_code==403
    assert client.post('/api/search',json={'asset':'x','frame':-1}).status_code==422
    j=client.post('/api/search',json={'asset':'x','frame':3}).json()['id']
    assert store.job(j)['state']=='queued'
    client.post(f'/api/jobs/{j}/cancel');assert store.job(j)['state']=='cancelled'
    client.post(f'/api/jobs/{j}/retry');assert store.job(j)['state']=='queued'

def test_adaptation_requires_real_source_separated_labels(tmp_path,monkeypatch):
    from matchcut.adaptation import fine_tune
    import pytest
    monkeypatch.setattr(store,'DATA',tmp_path);store.init()
    with pytest.raises(ValueError,match='review study'):fine_tune()

def test_worker_recovers_interrupted_jobs(tmp_path,monkeypatch):
    from matchcut.worker import Worker
    import threading,time
    monkeypatch.setattr(store,'DATA',tmp_path);store.init()
    key=store.enqueue('fixture',{});store.update_job(key,state='running')
    worker=Worker();worker.execute=lambda key,kind,body:{'fixture':True}
    thread=threading.Thread(target=worker.run);thread.start()
    try:
        deadline=time.monotonic()+3
        while time.monotonic()<deadline and store.job(key)['state']!='succeeded':time.sleep(.02)
        assert store.job(key)['result']=={'fixture':True}
    finally:worker.stop.set();thread.join()
