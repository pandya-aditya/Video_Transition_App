import fcntl, json, threading, time, traceback
from . import store,media
from .inference import Engine

class Cancelled(Exception):pass
class Worker:
    def __init__(self):self.stop=threading.Event();self.engine=None
    def progress(self,key,p):
        if store.job(key)['state']=='cancelled':raise Cancelled()
        store.update_job(key,progress=p)
    def execute(self,key,kind,body):
        if kind in ('index','search') and self.engine is None:self.engine=Engine()
        if kind=='index':
            a=media.import_file(body['path'],body.get('name'),body.get('family'))
            self.engine.index(a,lambda p:self.progress(key,p))
            return {'asset':a['id']}
        if kind=='adapt':
            from .adaptation import fine_tune
            return fine_tune(lambda p:self.progress(key,p))
        if kind=='search':return self.engine.search(store.asset(body['asset']),body['frame'],store.assets(),body.get('mode','combined'),body.get('nearby',True))
        if kind=='render':return media.render(store.asset(body['a']),body['ai'],store.asset(body['b']),body['bi'],body.get('framing','pad'),body.get('height',360),body.get('before',2),body.get('after',2))
        raise ValueError('Unknown job kind')
    def run(self):
        lock=(store.DATA/'worker.lock').open('w')
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return
        with store.connect() as db:db.execute("UPDATE jobs SET state='queued',progress=0,error='Recovered after worker interruption' WHERE state='running'")
        while not self.stop.is_set():
            with store.connect() as db:
                row=db.execute("SELECT * FROM jobs WHERE state='queued' ORDER BY created LIMIT 1").fetchone()
                if row:db.execute("UPDATE jobs SET state='running',error=NULL WHERE id=?",(row['id'],))
            if not row:self.stop.wait(.25);continue
            key=row['id']
            try:
                result=self.execute(key,row['kind'],json.loads(row['body']))
                self.progress(key,1)
                store.update_job(key,state='succeeded',result=result)
            except Cancelled:pass
            except Exception as exc:
                traceback.print_exc();store.update_job(key,state='failed',error=str(exc))
        lock.close()
