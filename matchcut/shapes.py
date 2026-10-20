"""Untrained geometric evidence for cross-object cuts; never a semantic label."""
import cv2
import numpy as np
from PIL import ImageOps

VERSION='round336-regions-v5'

def describe(image):
    gray=cv2.cvtColor(np.asarray(ImageOps.pad(image,(336,336))),cv2.COLOR_RGB2GRAY)
    gray=cv2.GaussianBlur(gray,(5,5),1)
    circles=cv2.HoughCircles(gray,cv2.HOUGH_GRADIENT,dp=1.2,minDist=24,
        param1=90,param2=28,minRadius=9,maxRadius=145)
    result=np.full((3,4),np.nan,dtype='float32')
    edges=cv2.dilate(cv2.Canny(gray,45,90),np.ones((3,3),np.uint8))
    gx=cv2.Sobel(gray,cv2.CV_32F,1,0,ksize=3);gy=cv2.Sobel(gray,cv2.CV_32F,0,1,ksize=3)
    theta=np.linspace(0,2*np.pi,120,endpoint=False); candidates=[]
    for x,y,r in ([] if circles is None else circles[0]):
        xs=np.rint(x+r*np.cos(theta)).astype(int);ys=np.rint(y+r*np.sin(theta)).astype(int)
        valid=(xs>=0)&(xs<336)&(ys>=0)&(ys<336)
        if valid.mean()<.8:continue
        # Texture and straight edges can vote for false circles. Require a
        # substantial circumference with gradients normal to the circle.
        radial=[]
        for delta in (-2,-1,0,1,2):
            xx=np.clip(np.rint(x+(r+delta)*np.cos(theta)).astype(int),0,335)
            yy=np.clip(np.rint(y+(r+delta)*np.sin(theta)).astype(int),0,335)
            dx=gx[yy,xx];dy=gy[yy,xx];magnitude=np.hypot(dx,dy)
            alignment=np.abs(dx*np.cos(theta)+dy*np.sin(theta))/np.maximum(magnitude,1e-5)
            radial.append((alignment>.88)&(magnitude>35)&(edges[yy,xx]>0))
        supported=np.any(radial,axis=0)&valid
        support=float(supported.mean())
        if support<.62:continue
        candidates.append((support,[x/336,y/336,r/336,support]))
    # Closed oval contours cover tilted pupils/marbles that Hough circles miss.
    contours,_=cv2.findContours(cv2.Canny(gray,35,90),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
    contours=list(contours)
    for threshold in (30,60,100,150,200,230):
        for kind in (cv2.THRESH_BINARY,cv2.THRESH_BINARY_INV):
            _,mask=cv2.threshold(gray,threshold,255,kind)
            found,_=cv2.findContours(mask,cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
            contours.extend(found)
    for contour in contours:
        if len(contour)<30:continue
        (x,y),(w,h),angle=cv2.fitEllipse(contour)
        if min(w,h)<18 or max(w,h)>290 or min(w,h)/max(w,h)<.45:continue
        points=contour[:,0].astype(float)-[x,y]
        theta_e=np.deg2rad(angle)
        xx=points[:,0]*np.cos(theta_e)+points[:,1]*np.sin(theta_e)
        yy=-points[:,0]*np.sin(theta_e)+points[:,1]*np.cos(theta_e)
        radial_distance=np.sqrt((xx/(w/2))**2+(yy/(h/2))**2)
        error=float(np.median(np.abs(radial_distance-1)))
        angles=np.arctan2(yy/(h/2),xx/(w/2))
        coverage=len(set(np.floor((angles+np.pi)/(2*np.pi)*16).astype(int).clip(0,15)))/16
        area_ratio=cv2.contourArea(contour)/(np.pi*w*h/4)
        if error>.075 or coverage<.875 or not .8<area_ratio<1.15:continue
        support=float(coverage*np.exp(-5*error));r=np.sqrt(w*h)/2
        if any(np.hypot(x-c[1][0]*336,y-c[1][1]*336)<8 and abs(r-c[1][2]*336)<8 for c in candidates):continue
        candidates.append((support,[x/336,y/336,r/336,support]))
    candidates.sort(key=lambda x:x[0],reverse=True)
    for i,(_,circle) in enumerate(candidates[:3]):result[i]=circle
    return result

def similarity(a,b):
    """Best supported circle alignment, including position and scale on padded frame."""
    best=None
    for x in a:
        for y in b:
            if not np.isfinite(x).all() or not np.isfinite(y).all():continue
            distance=np.linalg.norm(x[:2]-y[:2]);scale=abs(np.log(max(x[2],1e-5)/max(y[2],1e-5)))
            score=float(np.exp(-4*distance-1.2*scale)*np.sqrt(x[3]*y[3]))
            best=score if best is None else max(best,score)
    return best
