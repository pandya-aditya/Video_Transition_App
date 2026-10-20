"""Download explicitly licensed Commons videos, with source metadata and hashes."""
import hashlib, json, re, sys, time, ssl, certifi
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
ROOT=Path(__file__).resolve().parents[1]; dest=ROOT/'data/samples';dest.mkdir(parents=True,exist_ok=True)
TITLES=[
'File:Elzhana Taniyeva 2024 Sofia World Cup clubs handling.webm',
'File:Vaulting-gymnastics.webm',
'File:Basketball-Shot-Types-and-Shot-Success-in-Different-Levels-of-Competitive-Basketball-pone.0128885.s001.ogv',
]
def request(url):return urlopen(Request(url,headers={'User-Agent':'MatchCutPOC/0.1 (local video matching research)'}),timeout=90,context=ssl.create_default_context(cafile=certifi.where()))
def metadata(titles):
    params=dict(action='query',format='json',prop='imageinfo',titles='|'.join(titles),iiprop='url|size|sha1|extmetadata')
    with request('https://commons.wikimedia.org/w/api.php?'+urlencode(params)) as r:return json.load(r)['query']['pages'].values()
if __name__=='__main__':
    manifest=[]
    saved=json.loads((ROOT/'samples-manifest.json').read_text()) if (ROOT/'samples-manifest.json').exists() else []
    for page in metadata(sys.argv[1:] or [r['title'] for r in saved] or TITLES):
        if 'imageinfo' not in page:print('missing',page);continue
        info=page['imageinfo'][0];meta=info['extmetadata']
        license=meta.get('LicenseShortName',{}).get('value','')
        if not any(s in license for s in ('CC BY','CC0','Public domain')):raise ValueError(license)
        if info['size']>35_000_000:print('skip large',page['title']);continue
        path=dest/(str(page['pageid'])+Path(info['url']).suffix)
        if not path.exists():
            with request(info['url']) as r, path.with_suffix('.part').open('wb') as f:
                count=0
                while chunk:=r.read(1024*1024):
                    count+=len(chunk)
                    if count>35_000_000:raise ValueError('Download cap')
                    f.write(chunk)
            path.with_suffix('.part').replace(path)
        raw=path.read_bytes()
        if hashlib.sha1(raw).hexdigest()!=info['sha1']:raise ValueError('Source hash mismatch')
        entry=dict(title=page['title'],path=str(path.relative_to(ROOT)),url=info['url'],source=info['descriptionurl'],
            license=license,author=re.sub('<[^>]+>','',meta.get('Artist',{}).get('value','')),
            sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),family=str(page['pageid']))
        prior=next((r for r in saved if r['sha256']==entry['sha256']),{})
        for field in ('family','name'):
            if field in prior:entry[field]=prior[field]
        manifest.append(entry); print(entry['title'],len(raw),flush=True)
        oldpath=ROOT/'samples-manifest.json'
        old=json.loads(oldpath.read_text()) if oldpath.exists() else []
        entries={v['sha256']:v for v in old+manifest}
        oldpath.write_text(json.dumps(list(entries.values()),indent=2)+'\n')
        time.sleep(3)
    oldpath=ROOT/'samples-manifest.json'
    old=json.loads(oldpath.read_text()) if oldpath.exists() else []
    entries={v['sha256']:v for v in old+manifest}
    oldpath.write_text(json.dumps(list(entries.values()),indent=2)+'\n')
