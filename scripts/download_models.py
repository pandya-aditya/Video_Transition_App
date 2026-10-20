"""Explicit setup only: the application itself uses local files, never downloads."""
import json, os, certifi
os.environ["SSL_CERT_FILE"]=certifi.where()
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ['HF_HOME']=str(ROOT/'.cache/huggingface')
os.environ['TORCH_HOME']=str(ROOT/'data/models/torch')
from huggingface_hub import HfApi, snapshot_download
repo='facebook/dinov2-small'
lock=ROOT/'models.lock.json'
meta=json.loads(lock.read_text()) if lock.exists() else {'repo':repo,'revision':HfApi().model_info(repo).sha}
snapshot_download(repo,revision=meta['revision'],local_dir=ROOT/'data/models/dinov2-small',
                  allow_patterns=['config.json','preprocessor_config.json','model.safetensors','README.md'])
from torchvision.models.optical_flow import raft_small, Raft_Small_Weights
raft_small(weights=Raft_Small_Weights.C_T_V2)
meta['motion']='torchvision Raft_Small_Weights.C_T_V2'
import urllib.request, hashlib
pose_url='https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task'
pose_path=ROOT/'data/models/pose_landmarker_lite.task'
if not pose_path.exists():
    with urllib.request.urlopen(pose_url,timeout=60) as r:raw=r.read(10_000_000)
    if len(raw)>=10_000_000:raise ValueError('Unexpected model size')
    pose_path.write_bytes(raw)
pose_hash=hashlib.sha256(pose_path.read_bytes()).hexdigest()
if meta.get('pose',{}).get('sha256',pose_hash)!=pose_hash:raise ValueError('Pose checksum mismatch')
meta['pose']={'url':pose_url,'sha256':pose_hash,'license':'Apache-2.0','model_card':'https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf'}
lock.write_text(json.dumps(meta,indent=2)+'\n')
print(meta)
