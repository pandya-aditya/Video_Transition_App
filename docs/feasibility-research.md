# Match Cut: feasibility research

Inspected 2026-10-19 (America/Toronto). Preliminary research; no weights downloaded, no inference benchmark run, and no model selected. User priorities: composition/shape, movement direction and speed, pose, and secondary semantic connection across sports, film, and personal recordings.

## Candidate representations

| Candidate | Verified facts | Hypothesis to test and tradeoff |
| --- | --- | --- |
| DINOv2 ViT-S/14 (`facebook/dinov2-small`) | Meta documents 384-dimensional small-model features, class and patch tokens, 14-pixel patches, nearest-neighbor retrieval, and Apache-2.0 licensing. The hosted Safetensors file is 88.2 MB. | A compact first visual baseline. Compare normalized global features with spatially pooled patch features for composition. Neither global similarity nor patch similarity establishes pose correspondence or aesthetic quality. |
| SigLIP 2 Base (`google/siglip2-base-patch16-224`) | Google documents image embeddings and semantic/dense-feature objectives under Apache-2.0. The combined hosted checkpoint is 1.5 GB. | A possible semantic comparison, secondary to the user's visual priorities. Loading only a vision component does not guarantee a smaller download from a combined checkpoint. Run sequentially with DINOv2 if the agreed budget permits. |
| RAFT Small | Torchvision documents pretrained `C_T_V2` weights, 990,162 parameters, a 3.8 MB file, minimum 128×128 input, and paired-image transforms to [-1, 1]. | Learned temporal analysis candidate for shortlisted windows. Small weights do not imply low compute; measure actual M2 latency and memory. Select the explicit pretrained enum, not the constructor's untrained default. |
| Farnebäck optical flow | OpenCV provides dense motion estimation between adjacent frames without learned weights. | A classical motion baseline alongside genuine learned visual inference. Useful for an ablation; camera motion, occlusion, lighting changes, and large displacements can mislead it. |

Sources: [Meta DINOv2 model card](https://github.com/facebookresearch/dinov2/blob/main/MODEL_CARD.md), [DINOv2 weight artifact metadata](https://huggingface.co/facebook/dinov2-small/blob/main/model.safetensors), [Google SigLIP 2 model card](https://huggingface.co/google/siglip2-base-patch16-224), [SigLIP 2 weight artifact metadata](https://huggingface.co/google/siglip2-base-patch16-224/blob/main/model.safetensors), [Torchvision RAFT Small](https://docs.pytorch.org/vision/stable/models/generated/torchvision.models.optical_flow.raft_small.html), [OpenCV optical-flow tutorial](https://docs.opencv.org/4.x/d4/dee/tutorial_optical_flow.html).

DINOv3 is a possible later comparison. Its official repository describes requesting access to weights and uses a distinct DINOv3 license. Requiring it would conflict with the initial preference for avoiding access dependencies. This is a scope recommendation, not a claim that it is technically unsuitable. [Meta DINOv3 repository](https://github.com/facebookresearch/dinov3)

Pose is an unresolved representation question: patch features may retain spatial information but are not a validated pose estimator. Google's [MediaPipe Pose Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker) provides a concrete candidate with 33 landmarks, image/world coordinates, and Lite/Full/Heavy bundles. If approved examples require explicit human-joint alignment, compare visibility-weighted joint geometry against the visual baseline; multiple athletes, occlusion, and cropped bodies need failure cases. Confirm the exact bundle's license, Python/arm64 wheel support, download size, and runtime before selecting it. The [Python task guide](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/python) and [setup guide](https://developers.google.com/edge/mediapipe/solutions/setup_python) are starting points. Do not infer model-weight licensing from the documentation site's code-sample license.

## Hardware and model-loading experiment

The agreed target is an M2 MacBook Air with 16 GB memory, 10 GPU cores, and macOS 15.6.1. The default Python lacks PyTorch, but a discovered Python 3.11.9 installation has torch 2.5.1 and transformers 4.46.2. MPS was unavailable within the tool sandbox but available in a permitted unsandboxed check: deterministic 256×256 matrix multiplication produced finite outputs and matched CPU exactly. This confirms a basic accelerator execution path, not model throughput or universal operator support. Global packages were not changed. The [Apple PyTorch page](https://developer.apple.com/metal/pytorch/) and [PyTorch MPS documentation](https://docs.pytorch.org/docs/main/notes/mps.html) have release-specific prerequisites; select a mutually compatible pinned environment and check its own documentation.

After download and resource choices are answered:

1. Build an isolated environment. Check `torch.backends.mps.is_built()` and `is_available()`, then exercise each candidate on CPU and MPS. CPU fallback must be reported rather than silently presented as GPU performance.
2. Pin each checkpoint revision and processor configuration. Use the matching official preprocessing; evaluate any aspect-preserving variant separately because cropping/resizing changes composition.
3. Load one encoder at a time; call `eval()` and inference mode; begin with bounded small batches. Use warmup and accelerator synchronization when timing GPU work.
4. Measure cold load, decode, preprocessing, inference, retrieval, ranking, preview rendering, export, process memory, and artifact growth separately. Include cold versus cached search and repeated-run variance.
5. Check finite vectors, shape, normalization, and sampled CPU/MPS agreement before trusting rankings. Weight-file size is not a runtime memory estimate.

APIs to verify against pinned packages: [Transformers DINOv2](https://huggingface.co/docs/transformers/model_doc/dinov2) and [Transformers SigLIP2](https://huggingface.co/docs/transformers/model_doc/siglip2). The specific fixed-resolution checkpoint's configuration takes precedence over assuming every feature of the broader SigLIP 2 family is available.

## Proposed thin experiment, pending scope and footage

Use approved real clips with selected outgoing timestamps and user-marked useful/rejected candidates. Keep source families, alternate encodes, and neighboring moments together when splitting tuning and evaluation.

- Retrieve using a normalized global embedding baseline and exact dot products. At a small collection size, an additional vector service is a hypothesis requiring evidence, not a prerequisite.
- Compare global-only retrieval with a union that includes spatial composition features. A temporal reranker cannot recover an aesthetically useful candidate missing from retrieval.
- For each A → B candidate, analyze forward motion leading into A and forward motion leaving B. Do not compute optical flow across unrelated clips or treat reversed playback as equivalent.
- Retain spatial motion information so rotations do not vanish through whole-frame averaging. Normalize displacement by elapsed source time and frame dimensions. Record x-right/y-down coordinates, rotation handling, padding masks, and stationary-motion behavior.
- Compare appearance-only ranking with appearance plus temporal/composition ranking. Keep component scores, feature normalization, and heuristic ranking weights explicit; they are not calibrated probabilities.
- Render actual ordered transitions, then compare user preferences. Evaluate retrieval coverage separately from final top-k usefulness. Numeric acceptance targets remain an interview decision.
- If results fail, inspect sampling, representation, retrieval recall, and temporal scoring separately. Camera movement and subject movement need separate diagnostics before adding segmentation or stabilization.

The user has now accepted small-demo targets of ≤5-minute indexing, ≤3-second ranked search, and ≤5-second first playable preview; these are not measured results. The quality gate is 8–10 outgoing moments, a keepable match among six results for at least half, plus three convincing exports. Budgets are $0 services, ≤2 GB weights, and ≤10 GB total working disk. Sampling intervals and ranking weights remain engineering hypotheses to test.

## Required adaptation experiment

The user explicitly chose fine-tuning a small part of the pretrained visual encoder, not merely fitting a new ranking head. Proposed implementation: freeze most of DINOv2 and update a bounded subset of its final transformer block using user usefulness labels and pairwise preferences. Select the exact trainable tensors and learning rate from a small pilot; record trainable counts, gradient/weight changes, seed, data split, and optimizer configuration. Preserve the original checkpoint and version adapted feature caches separately.

Obtain real user labels through playable review before training. Include ties/skip and distinguish appearance appeal from temporal continuity. Prefer a regularized pairwise objective and early stopping on a separate validation group. Keep every source family wholly within one split, with neither side of a held-out transition contributing to tuning. Small collections may require a few more sources rather than leaking adjacent frames across splits; expansion stays inside the agreed disk budget.

Evaluate frozen versus adapted encoders with fixed retrieval depth, timing settings, and motion method; compare recall and actual top-six usefulness separately. A trained checkpoint is a learning deliverable even if it loses to the frozen model. Do not promote it to the default or claim improvement without held-out evidence. User rating availability is agreed, but no labels exist yet.

## Media correctness and storage implications

[PyAV's timing documentation](https://pyav.org/docs/stable/api/time.html) describes integer presentation timestamps multiplied by rational time bases and distinct decoding/encoding time contexts. The linked stable page identifies itself as 9.0.2; implementation must additionally check the installed release.

Proposed checks for the eventual pipeline:

- Preserve source PTS and time base, stream start offset, rotation, and a normalized timeline. Do not infer variable-rate timestamps from frame index divided by nominal fps.
- Define cut inclusion precisely: which frame ends A and which frame starts B. Seek then decode to the selected frame; a keyframe seek alone is insufficient.
- Use one edit specification for previews and exports; test content equivalence around the cut. Agree on framing, audio, output fps, and trim precision first.
- Keep temporal windows inside shots with adequate pre/post-roll. The need and scope of shot detection depend on interview item 9.
- Key feature caches by source identity, timestamp/window, weights revision, preprocessing, and temporal configuration. Ranking-weight changes should reuse features.
- Keep source files separate from clearable derived artifacts. Import copies versus references is unresolved.

All these are proposed engineering controls. Real footage and genuine inference are required for aesthetic evaluation; labeled synthetic fixtures establish timing and recovery behavior only.
