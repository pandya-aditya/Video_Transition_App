from pathlib import Path
import hashlib, json, os, sqlite3, time, uuid

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get('MATCHCUT_DATA', ROOT / 'data')).resolve()
for part in ('media', 'artifacts', 'models', 'features', 'uploads'):
    (DATA / part).mkdir(parents=True, exist_ok=True)

def connect():
    db = sqlite3.connect(DATA / 'matchcut.sqlite', timeout=30)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA journal_mode=WAL')
    return db

def init():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS assets(id TEXT PRIMARY KEY, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, kind TEXT, body TEXT,
          state TEXT, progress REAL DEFAULT 0, result TEXT, error TEXT, created REAL);
        CREATE TABLE IF NOT EXISTS labels(id TEXT PRIMARY KEY, body TEXT, created REAL);
        ''')

def ident(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:24]

def assets():
    with connect() as db:
        return [json.loads(r['body']) for r in db.execute('SELECT body FROM assets')]

def asset(key):
    with connect() as db:
        row = db.execute('SELECT body FROM assets WHERE id=?', (key,)).fetchone()
    if not row: raise ValueError('Unknown asset')
    return json.loads(row['body'])

def save_asset(value):
    with connect() as db:
        db.execute('INSERT OR REPLACE INTO assets VALUES (?,?)', (value['id'], json.dumps(value)))

def enqueue(kind, body):
    key = uuid.uuid4().hex
    with connect() as db:
        db.execute('INSERT INTO jobs(id,kind,body,state,created) VALUES (?,?,?,?,?)',
                   (key, kind, json.dumps(body), 'queued', time.time()))
    return key

def job(key):
    with connect() as db:
        row = db.execute('SELECT * FROM jobs WHERE id=?', (key,)).fetchone()
    if not row: raise ValueError('Unknown job')
    out = dict(row)
    for k in ('body', 'result'):
        out[k] = json.loads(out[k]) if out[k] else None
    return out

def update_job(key, **fields):
    allowed = {'state','progress','result','error'}
    assert set(fields) <= allowed
    if 'result' in fields: fields['result'] = json.dumps(fields['result'])
    with connect() as db:
        db.execute('UPDATE jobs SET '+','.join(f'{k}=?' for k in fields)+' WHERE id=?',
                   [*fields.values(), key])

def check_budget(extra=0):
    # Count retained files once by inode (uv hardlinks are shared).
    seen, size = set(), 0
    for base in (ROOT,):
        for p, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d != '.git']
            for name in files:
                try:
                    s = (Path(p)/name).stat()
                    inode = (s.st_dev,s.st_ino)
                    if inode not in seen: size += s.st_size; seen.add(inode)
                except FileNotFoundError: pass
    if size + extra > 10_000_000_000: raise ValueError('10 GB workspace budget exceeded')
    return size
