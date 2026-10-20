import io, json, threading, uuid
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from . import store,media
from .worker import Worker

@asynccontextmanager
async def lifespan(app):
    store.init();worker=Worker();thread=threading.Thread(target=worker.run,daemon=True);thread.start()
    yield
    worker.stop.set();thread.join(timeout=5)

app=FastAPI(title='Match Cut',lifespan=lifespan)
@app.middleware('http')
async def local_only(request:Request,call_next):
    host=request.headers.get('host','').split(':')[0]
    origin=request.headers.get('origin')
    if host not in ('127.0.0.1','localhost','testserver') or (origin and origin not in ('http://127.0.0.1:8765','http://localhost:8765')):
        return Response('Local origin required',status_code=403)
    return await call_next(request)

@app.exception_handler(ValueError)
async def invalid(request,exc):return Response(str(exc),status_code=400)

@app.get('/api/assets')
def assets():return store.assets()
@app.get('/api/jobs')
def jobs():
    with store.connect() as db:ids=[r['id'] for r in db.execute('SELECT id FROM jobs ORDER BY created DESC LIMIT 30')]
    return [store.job(i) for i in ids]
@app.get('/api/jobs/{key}')
def job(key:str):return store.job(key)
@app.post('/api/jobs/{key}/cancel')
def cancel(key:str):
    if store.job(key)['state'] in ('queued','running'):store.update_job(key,state='cancelled')
    return store.job(key)
@app.post('/api/import')
async def upload(file:UploadFile=File(...)):
    store.check_budget(1_000_000_000)
    path=store.DATA/'uploads'/(uuid.uuid4().hex+Path(file.filename or '.mp4').suffix)
    count=0
    try:
        with path.open('wb') as f:
            while chunk:=await file.read(1024*1024):
                count+=len(chunk)
                if count>500_000_000:raise ValueError('500 MB file limit')
                f.write(chunk)
    except BaseException:path.unlink(missing_ok=True);raise
    return {'id':store.enqueue('index',{'path':str(path),'name':Path(file.filename or 'Clip').stem})}
@app.post('/api/sync-videos')
def sync_videos():
    folder=store.ROOT/'Videos'
    if not folder.is_dir():raise ValueError('Create a Videos folder in this workspace first')
    return {'id':store.enqueue('index-folder',{'path':str(folder),'collection':'targeted'})}

class Search(BaseModel):
    asset:str
    frame:int=Field(ge=0)
    mode:str='combined'
    nearby:bool=True
    refine:bool=True
    collection:str='all'
    before:float=Field(default=2,ge=.25,le=5)
    after:float=Field(default=2,ge=.25,le=5)
@app.post('/api/search')
def search(body:Search):
    if body.mode not in ('combined','appearance','shape'):raise ValueError('Unknown ranking mode')
    return {'id':store.enqueue('search',body.model_dump())}
class Edit(BaseModel):
    a:str;ai:int=Field(ge=0);b:str;bi:int=Field(ge=0)
    framing:str='pad';height:int=360
    before:float=Field(default=2,ge=.25,le=5)
    after:float=Field(default=2,ge=.25,le=5)
@app.post('/api/render')
def render(body:Edit):return {'id':store.enqueue('render',body.model_dump())}
@app.get('/api/frame/{key}/{index}')
def frame(key:str,index:int):
    a=store.asset(key)
    if not 0<=index<len(a['times']):raise ValueError('Invalid source frame')
    im=media.frames(a,[index])[0];im.thumbnail((960,540));buf=io.BytesIO();im.save(buf,format='JPEG',quality=90)
    return Response(buf.getvalue(),media_type='image/jpeg')
@app.get('/api/source/{key}')
def source(key:str):return FileResponse(store.asset(key)['path'])
@app.post('/api/labels')
async def label(request:Request):
    body=await request.json()
    if body.get('kind') not in ('usefulness','preference'):raise ValueError('Unknown label kind')
    # Store the exact edit/version shown, not mutable UI state.
    if not isinstance(body.get('edit'),dict):raise ValueError('An edit specification is required')
    key=uuid.uuid4().hex
    import time
    with store.connect() as db:db.execute('INSERT INTO labels VALUES (?,?,?)',(key,json.dumps(body),time.time()))
    return {'id':key}
@app.get('/api/labels')
def labels():
    with store.connect() as db:return [json.loads(r['body']) for r in db.execute('SELECT body FROM labels')]
@app.post('/api/jobs/{key}/retry')
def retry(key:str):
    if store.job(key)['state'] in ('failed','cancelled'):
        store.update_job(key,state='queued',progress=0,error=None)
    return store.job(key)

@app.get('/api/review')
def review(collection:str='all'):
    path=store.DATA/'review-study.json'
    if not path.exists():return []
    rows=json.loads(path.read_text())
    if collection!='all':
        from .library import select_collection
        ids={a['id'] for a in select_collection(store.assets(),collection)}
        rows=[r for r in rows if r['edit']['a'] in ids and r['left']['b'] in ids and r['right']['b'] in ids]
    with store.connect() as db:
        done={json.loads(r['body']).get('review_id') for r in db.execute('SELECT body FROM labels')}
    return [{k:v for k,v in r.items() if not k.endswith('_method')} for r in rows if r['id'] not in done]

class Preference(BaseModel):
    review_id:str
    value:str
@app.post('/api/review')
def preference(body:Preference):
    if body.value not in ('left','right','tie','neither','skip'):raise ValueError('Invalid preference')
    rows=json.loads((store.DATA/'review-study.json').read_text())
    row=next((r for r in rows if r['id']==body.review_id),None)
    if not row:raise ValueError('Unknown review')
    import time
    value=dict(row,review_id=body.review_id,kind='preference',value=body.value)
    with store.connect() as db:
        db.execute('INSERT OR REPLACE INTO labels VALUES (?,?,?)',('review-'+body.review_id,json.dumps(value),time.time()))
    return {'saved':True}

@app.post('/api/adapt')
def adapt():return {'id':store.enqueue('adapt',{})}

app.mount('/artifacts',StaticFiles(directory=store.DATA/'artifacts'),name='artifacts')
if (store.ROOT/'web/dist').exists():app.mount('/',StaticFiles(directory=store.ROOT/'web/dist',html=True),name='web')
