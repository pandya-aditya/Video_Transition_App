from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from matchcut import shapes,library,store

def test_circle_alignment_and_missing_evidence():
    def circle(x=168,r=65):
        im=Image.new('RGB',(336,336),'black');ImageDraw.Draw(im).ellipse((x-r,168-r,x+r,168+r),fill='white');return shapes.describe(im)
    a=circle();same=circle();shifted=circle(90,30)
    assert shapes.similarity(a,same)>.75
    assert shapes.similarity(a,shifted)<shapes.similarity(a,same)
    assert shapes.similarity(a,shapes.describe(Image.new('RGB',(336,336),'black'))) is None

def test_collection_isolation():
    rows=[{'id':'a','collections':['targeted']},{'id':'b','attribution':{'license':'CC0'}},{'id':'c','collections':['another']}]
    assert [r['id'] for r in library.select_collection(rows,'targeted')]==['a']
    assert [r['id'] for r in library.select_collection(rows,'samples')]==['b']
    assert library.select_collection(rows,'all')==rows

def test_folder_import_is_repeatable_and_does_not_follow_links(tmp_path,monkeypatch):
    folder=tmp_path/'Videos';folder.mkdir();(folder/'one.mp4').write_bytes(b'fixture');(folder/'notes.txt').write_text('not footage')
    outside=tmp_path/'outside.mp4';outside.write_bytes(b'fixture');(folder/'link.mp4').symlink_to(outside)
    saved={};calls=[]
    monkeypatch.setattr(library.media,'import_file',lambda path:dict(saved.get(path.name,{'id':path.name,'name':path.stem})))
    monkeypatch.setattr(store,'save_asset',lambda a:saved.update({a['id']:a.copy()}))
    class Engine:
        def index(self,a,progress):calls.append(a['id']);progress(1)
    for _ in range(2):assert library.import_folder(folder,'targeted',Engine())==['one.mp4']
    assert saved['one.mp4']['collections']==['targeted']
    assert 'link.mp4' not in calls
