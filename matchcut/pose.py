import os
from pathlib import Path
import numpy as np
from PIL import ImageOps
from .store import DATA
os.environ.setdefault('MPLCONFIGDIR',str(DATA/'matplotlib'))

class Pose:
    def __init__(self):
        import mediapipe as mp
        self.mp=mp
        options=mp.tasks.vision.PoseLandmarkerOptions(base_options=mp.tasks.BaseOptions(model_asset_path=str(DATA/'models/pose_landmarker_lite.task')),
            num_poses=1,min_pose_detection_confidence=.5,min_pose_presence_confidence=.5)
        self.detector=mp.tasks.vision.PoseLandmarker.create_from_options(options)
    def infer(self,image):
        padded=np.asarray(ImageOps.pad(image,(256,256)))
        result=self.detector.detect(self.mp.Image(image_format=self.mp.ImageFormat.SRGB,data=padded))
        if not result.pose_landmarks:return np.full((12,3),np.nan,dtype='float32')
        p=result.pose_landmarks[0]
        return np.array([[p[i].x,p[i].y,p[i].visibility] for i in (11,12,13,14,15,16,23,24,25,26,27,28)],dtype='float32')

def similarity(a,b):
    valid=np.isfinite(a).all(axis=1)&np.isfinite(b).all(axis=1)&(a[:,2]>.6)&(b[:,2]>.6)
    if valid.sum()<6:return None
    # Screen-space agreement includes subject position/size, without mirror invariance.
    distance=np.linalg.norm(a[valid,:2]-b[valid,:2],axis=1).mean()
    return float(np.exp(-distance/.15))
