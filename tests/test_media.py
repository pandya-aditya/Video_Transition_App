from fractions import Fraction
import av,numpy as np,pytest
from matchcut import media

def fixture(path,variable=False):
    with av.open(str(path),'w') as c:
        s=c.add_stream('libx264',rate=30);s.width=96;s.height=64;s.pix_fmt='yuv420p';s.time_base=Fraction(1,90000)
        pts=0
        for i in range(180):
            arr=np.zeros((64,96,3),dtype=np.uint8);arr[:]=[40+i%100,90,130];arr[:,i%90:i%90+5]=[255,0,0]
            f=av.VideoFrame.from_ndarray(arr,format='rgb24');f.pts=pts;f.time_base=Fraction(1,90000)
            pts+=4500 if variable and i%2 else 3000
            for p in s.encode(f):c.mux(p)
        for p in s.encode():c.mux(p)
    return dict(path=str(path),id=path.stem,**media.probe(path))

@pytest.mark.parametrize('variable',[False,True])
def test_pts_selection_and_exact_boundaries(tmp_path,monkeypatch,variable):
    monkeypatch.setattr(media,'DATA',tmp_path);(tmp_path/'artifacts').mkdir()
    a=fixture(tmp_path/'a.mp4',variable);b=fixture(tmp_path/'b.mp4',variable)
    ai=media.nearest(a,2.5);bi=media.nearest(b,1)
    assert a['pts'][ai]*Fraction(*a['time_base']) == pytest.approx(a['times'][ai])
    source=media.frames(a,[ai,ai-1]);assert not np.array_equal(source[0],source[1])
    out=media.render(a,ai,b,bi)
    with av.open(str(tmp_path/out['url'].lstrip('/'))) as c:
        assert not c.streams.audio
        frames=list(c.decode(video=0))
        assert len(frames)==120
        from PIL import ImageOps
        for idx,im in [(59,source[0]),(60,media.frames(b,[bi])[0])]:
            expected=np.array(ImageOps.pad(im,(640,360),color='black')).astype(float)
            actual=frames[idx].to_ndarray(format='rgb24').astype(float)
            assert np.abs(expected-actual).mean()<7
    assert media.render(a,ai,b,bi)['cached']
    with pytest.raises(ValueError):media.window(a,0,'out')

def test_shot_context():
    a=dict(times=[i/10 for i in range(100)],duration=10,cuts=[0,50,100])
    with pytest.raises(ValueError):media.window(a,55,'out')
    with pytest.raises(ValueError):media.window(a,40,'in')
    assert media.window(a,75,'out')[1]==76

def test_rotation_matches_ffmpeg_display(tmp_path):
    import subprocess
    from PIL import Image
    original=tmp_path/'normal.mp4';fixture(original)
    rotated=tmp_path/'rotated.mp4'
    subprocess.run([media.FFMPEG,'-v','error','-display_rotation','90','-i',str(original),'-c','copy',str(rotated)],check=True)
    a=dict(id='rotated',path=str(rotated),**media.probe(rotated))
    expected=tmp_path/'display.png'
    subprocess.run([media.FFMPEG,'-v','error','-i',str(rotated),'-frames:v','1',str(expected)],check=True)
    actual=media.frames(a,[0])[0]
    assert actual.size==Image.open(expected).size==(64,96)
    assert np.abs(np.asarray(actual).astype(float)-np.asarray(Image.open(expected)).astype(float)).mean()<3
