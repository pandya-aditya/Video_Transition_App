"""Explicit local folder ingestion. Never scans outside the supplied folder."""
from pathlib import Path
from . import store,media

VIDEO_SUFFIXES={'.mp4','.mov','.webm','.ogv','.ogg','.mkv','.m4v'}

def import_folder(folder,collection,engine,progress=lambda p:None):
    folder=Path(folder).resolve()
    if not folder.is_dir():raise ValueError('Video folder does not exist')
    files=sorted(p for p in folder.iterdir() if p.is_file() and not p.is_symlink() and p.suffix.lower() in VIDEO_SUFFIXES)
    if not files:raise ValueError('No supported videos in this folder')
    output=[]
    for n,path in enumerate(files):
        a=media.import_file(path)
        # Preserve memberships on deduplicated imports; the original is untouched.
        a['collections']=sorted(set(a.get('collections',[])+[collection]))
        a.setdefault('attribution',None)
        store.save_asset(a)
        engine.index(a,lambda p:progress((n+p)/len(files)))
        output.append(a['id']);progress((n+1)/len(files))
    return output

def select_collection(assets,collection):
    if collection=='all':return assets
    if collection=='samples':return [a for a in assets if a.get('attribution') and 'targeted' not in a.get('collections',[])]
    return [a for a in assets if collection in a.get('collections',[])]
