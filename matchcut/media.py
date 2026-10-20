"""Source frame identities are decode indices + integer PTS, never fps*time."""
import bisect, hashlib, json, math, shutil, subprocess, re
from pathlib import Path
import av, cv2, imageio_ffmpeg, numpy as np
from PIL import Image, ImageOps
from .store import DATA, ident, assets, save_asset, check_budget

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def oriented(frame, max_size=None, rotation=0):
    if max_size and max(frame.width,frame.height)>max_size:
        scale=max_size/max(frame.width,frame.height)
        frame=frame.reformat(width=max(2,round(frame.width*scale)),height=max(2,round(frame.height*scale)),format='rgb24')
    image = frame.to_image()
    if rotation: image = image.rotate(rotation, expand=True)
    return image

def probe(path):
    # PyAV 16 does not expose stream display matrices. Read FFmpeg's display
    # rotation once; never silently discard phone orientation metadata.
    info=subprocess.run([FFMPEG,'-hide_banner','-i',str(path)],capture_output=True,text=True).stderr
    found=re.search(r'rotation of (-?[0-9.]+) degrees',info)
    rotation=float(found.group(1)) if found else 0
    if abs(rotation/90-round(rotation/90))>.001:raise ValueError('Only right-angle display rotations are supported')
    pts, times, cuts, previous = [], [], [0], None
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        if len(container.streams.video)!=1:raise ValueError('Import a file with one video stream')
        tb = stream.time_base
        for i, frame in enumerate(container.decode(stream)):
            if frame.pts is None: raise ValueError('Source has missing presentation timestamps')
            pts.append(frame.pts); times.append(float(frame.pts * tb))
            small = np.asarray(oriented(frame,48,rotation).resize((48, 48))).astype(float)
            # Conservative scene-change guard; dissolves and subtle cuts can escape it.
            if previous is not None and np.abs(small-previous).mean() > 45: cuts.append(i)
            previous = small
        rate = float(stream.average_rate or 30)
        width, height = oriented(frame,rotation=rotation).size if pts else (0,0)
    if len(pts) < 2: raise ValueError('Need at least two decoded frames')
    if any(b <= a for a,b in zip(times,times[1:])): raise ValueError('Non-increasing source timestamps')
    origin = times[0]
    times = [t-origin for t in times]
    duration = times[-1] + (times[-1]-times[-2])
    return dict(pts=pts, times=times, time_base=[tb.numerator,tb.denominator],
                origin=origin, duration=duration, fps=rate, width=width, height=height,
                cuts=sorted(set(cuts+[len(pts)])),rotation=rotation)

def frames(asset, indices, max_size=960):
    wanted = set(map(int, indices)); result = {}
    if not wanted or min(wanted)<0 or max(wanted)>=len(asset['pts']):
        raise ValueError('Frame index outside source')
    by_pts={asset['pts'][i]:i for i in wanted}
    with av.open(asset['path']) as c:
        stream=c.streams.video[0]
        c.seek(min(by_pts),stream=stream,backward=True,any_frame=False)
        for f in c.decode(stream):
            if f.pts in by_pts: result[by_pts[f.pts]] = oriented(f,max_size,asset.get('rotation',0))
            if len(result) == len(wanted): break
    if len(result) != len(wanted): raise ValueError('Could not decode requested source PTS')
    return [result[int(i)] for i in indices]

def nearest(asset, seconds):
    t = asset['times']; i = bisect.bisect_left(t, seconds)
    return min((max(0,i-1),min(len(t)-1,i)), key=lambda j:abs(t[j]-seconds))

def shot_bounds(asset, i):
    cuts = asset['cuts']; s = bisect.bisect_right(cuts, i)-1
    return cuts[s], cuts[s+1]

def window(asset, i, side, seconds=2.):
    if not 0 <= i < len(asset['times']): raise ValueError('Invalid source frame')
    t = asset['times']; lo, hi = shot_bounds(asset,i)
    end = t[i+1] if i+1 < len(t) else asset['duration']
    if side == 'out':
        start = end-seconds
        if start < t[lo]-1e-6: raise ValueError('Not enough outgoing context inside this shot')
        return bisect.bisect_left(t,start-1e-7), i+1
    finish = t[hi] if hi < len(t) else asset['duration']
    if t[i]+seconds > finish+1e-6: raise ValueError('Not enough incoming context inside this shot')
    return i, bisect.bisect_left(t, t[i]+seconds-1e-7)

def import_file(path, name=None, family=None, attribution=None):
    path = Path(path)
    if path.stat().st_size > 500_000_000: raise ValueError('500 MB per-file limit')
    check_budget(path.stat().st_size*3)
    digest = hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()
    existing = assets()
    if any(a['id']==digest for a in existing): return next(a for a in existing if a['id']==digest)
    if len(existing)>=20: raise ValueError('20 clip collection limit')
    meta = probe(path)
    if sum(a['duration'] for a in existing)+meta['duration']>600: raise ValueError('10 minute collection limit')
    target = DATA/'media'/f'{digest}{path.suffix.lower()}'
    shutil.copy2(path,target)
    a = dict(id=digest, name=name or path.stem, family=family or digest,
             path=str(target), attribution=attribution, status='imported', **meta)
    thumb = DATA/'artifacts'/f'{digest}.jpg'
    im=frames(a,[nearest(a,meta['duration']/2)])[0]; im.thumbnail((480,270)); im.save(thumb)
    a['thumbnail']='/artifacts/'+thumb.name
    save_asset(a)
    return a

def render(a, ai, b, bi, framing='pad', height=360, before=2., after=2.):
    if framing not in ('pad','crop'): raise ValueError('Invalid framing')
    if height not in (360,1080): raise ValueError('Invalid render size')
    ar=window(a,ai,'out',before); br=window(b,bi,'in',after)
    spec=dict(a=a['id'],ai=ai,b=b['id'],bi=bi,framing=framing,height=height,
              before=before,after=after,renderer='pts-boundary-v3-30fps')
    target=DATA/'artifacts'/f'{ident(spec)}.mp4'
    if target.exists(): return dict(url='/artifacts/'+target.name, spec=spec, cached=True)
    check_budget(100_000_000)
    width=height*16//9; temp=target.with_suffix('.partial.mp4')
    cmd=[FFMPEG,'-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24',
         '-s',f'{width}x{height}','-r','30','-i','-','-an','-c:v','libx264','-preset','veryfast',
         '-crf','20' if height==1080 else '24','-pix_fmt','yuv420p','-movflags','+faststart',str(temp)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for source,(start,end),duration,side in ((a,ar,before,'out'),(b,br,after,'in')):
            t=source['times']; count=max(1,round(duration*30))
            base=(t[end] if end<len(t) else source['duration'])-duration if side=='out' else t[start]
            ids=[max(start,min(end-1,bisect.bisect_right(t,base+k/30)-1)) for k in range(count)]
            if side=='out': ids[-1]=end-1
            else: ids[0]=start
            ims=frames(source,sorted(set(ids)),max_size=width); mapping=dict(zip(sorted(set(ids)),ims))
            for idx in ids:
                im=mapping[idx]
                im=ImageOps.fit(im,(width,height)) if framing=='crop' else ImageOps.pad(im,(width,height),color='black')
                proc.stdin.write(im.tobytes())
        proc.stdin.close(); error=proc.stderr.read().decode(); code=proc.wait()
        if code: raise RuntimeError(error)
        temp.replace(target)
    except BaseException:
        proc.kill(); proc.wait(); temp.unlink(missing_ok=True); raise
    return dict(url='/artifacts/'+target.name,spec=spec,cached=False)
