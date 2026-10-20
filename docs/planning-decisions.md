# Match Cut planning decisions

Updated: 2026-10-19 (America/Toronto). Planning interview complete; implementation authorized and starting.

The design brief contains proposals, not accepted defaults. Each of its 27 interview items is tracked below. **Answered** means the user supplied the material choice; **delegated** means the user explicitly handed it over; **unresolved** means a response or consequential detail is still needed. An unanswered recommendation never becomes a decision through elapsed time.

## Explicit instructions already established

- Build Match Cut as a personal creative application; the workspace name does not constrain the subjects. Keep the workspace in place.
- Local POC implementation is authorized once material planning choices are answered or delegated; no additional routine build approval is needed.
- Use real pretrained inference, cheap candidate retrieval, and more expensive ordered temporal ranking. Test usefulness with playable transitions before a large UI investment.
- Preserve source timing and preview/export alignment; version derived features by model and configuration.
- Include meaningful tests, actual performance measurements, a small quality comparison, setup instructions, architecture notes, and a demo script. Report failures honestly.
- During unresolved planning, do not inspect unrelated personal files, download large model weights, spend money, or upload footage.

## Safely observed facts

- Workspace initially contains only `MATCH_CUT_DESIGN.md` and `MATCH_CUT_POC_PROMPT.md`; no footage, existing implementation, or dependency manifests.
- No `AGENTS.md` found in this workspace or its ancestor directories. The directory is not a Git repository.
- MacBook Air (Mac14,2), Apple M2, 8 CPU cores, 10 GPU cores, 16 GB memory; Metal supported. macOS 15.6.1, arm64. Hardware identifiers were omitted from captured output.
- Approximately 110 GiB available on the workspace volume at inspection; this is not an agreed storage budget.
- PATH tooling: Python 3.13.3, uv 0.9.17, Node 25.4.0, npm 11.7.0, Git 2.52.0; Homebrew and pnpm available.
- `ffmpeg` and `ffprobe` are not on PATH. The default Python 3.13 lacks torch, torchvision, transformers, NumPy, PyAV, OpenCV, FastAPI, and uvicorn; pytest 8.4.2 is installed.
- A second interpreter, discovered through the installed uv location, is Python 3.11.9 at `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11`. It contains torch 2.5.1 and transformers 4.46.2, but not torchvision, PyAV, OpenCV, MediaPipe, or imageio-ffmpeg. No global packages were changed.
- PyTorch MPS is built but appears unavailable inside the tool sandbox. A permitted check outside the sandbox confirmed MPS availability and exact CPU/GPU agreement for a deterministic 256×256 matrix multiplication (finite output, max absolute difference 0). This is a capability sanity check, not a model benchmark or a guarantee of model/operator compatibility.
- A supplemental `sysctl` query was denied by the sandbox; hardware facts above came from `system_profiler`. No escalation was necessary.

## A. Creative purpose and first experience

| ID | Interview item | Status | Answer, proposal, or remaining detail |
| --- | --- | --- | --- |
| 1 | Enjoyable footage and specific interests | answered | Sports, film, and personal recordings. User wrote “sports, film, and person recordings.” |
| 2 | Own edits or a demo others can try | answered | Own edits first; a demo others can watch. |
| 3 | Selected outgoing moment or automatic pair discovery | answered | Select an outgoing moment and find its next shot. |
| 4 | What makes a cut satisfying; concrete examples | answered | Shape/composition, motion direction and speed, pose, with some semantic consideration. Accepted starting hypotheses: jumping athlete → similarly raised arms; sports movement → same-direction film character movement; turning body/round object → similarly positioned rotation in another scene. These are targets to test, not promised matches. |
| 5 | Hard cuts versus speed changes, beats, fades, effects | answered | Normal-speed hard cuts. |
| 6 | Ranked previews, two-clip export, or multi-clip sequence | answered | Ranked playable previews plus a two-clip export. |

## B. Footage, timing, and controls

| ID | Interview item | Status | Answer, proposal, or remaining detail |
| --- | --- | --- | --- |
| 7 | Available footage, approved locations, reusable samples, diagnostic fixtures | delegated | User: “find your own reusable public samples to start with.” Research and select public samples; record asset sources and licenses. No personal folders approved. Clearly labeled synthetic timing/recovery tests are within the requested verification scope, not aesthetic evidence. |
| 8 | Video count, duration, resolution/fps, mixed orientations | delegated | User delegated collection sizing to optimize effectiveness, latency, demo impact, and implementability. Initial working choice: 12–16 mostly single-shot clips, roughly 2–4 minutes total, 720p/1080p with varied native frame rates; include a few portrait clips for framing correctness. Adjust from actual benchmark evidence. No capacity claim. |
| 9 | Single shots, edited videos, gameplay, or mixture | answered | Mostly single-shot clips. Keep cut-crossing safeguards; broad edited-video segmentation is not the primary workflow. |
| 10 | Scrubbing, ranges, automatic moments, frame-accurate trimming | answered | Scrub and adjust by individual source frames on either side of the cut. |
| 11 | Pre/post-cut playback context and timing suggestions | answered | Two seconds each side; offer nearby timing suggestions. Proposed ±0.5-second search neighborhood accepted in context; controls remain adjustable within valid bounds. |
| 12 | Aspect-ratio treatment and export resolution/format | answered | Preserve with padding, optional crop-to-fill, 1080p H.264 MP4. |
| 13 | Source audio, silence, or music | answered | Mute previews and exports. |
| 14 | Same-source exclusion, near duplicates, diversity | answered | Exclude same source and duplicates; favor six different clips. Show fewer when insufficient eligible sources exist. |

## C. Inference and operational constraints

| ID | Interview item | Status | Answer, proposal, or remaining detail |
| --- | --- | --- | --- |
| 15 | Confirm observed hardware; same machine for demo | answered | Develop and demo on this M2 MacBook Air, 16 GB, 8 CPU/10 GPU cores, macOS 15.6.1. |
| 16 | Local processing, hosted workers, footage leaving machine | answered | Keep footage and inference entirely local. Browser UI bound to the local machine; internet allowed for setup/sample/model downloads. |
| 17 | Spending cap and model-download permission/budget | answered | $0 paid services; up to 2 GB model weights; 10 GB total local working storage for environment, footage, and derived files. These are caps, not consumption targets. Model downloads within this budget are authorized. |
| 18 | Indexing time, search latency, queued waits | answered | Accepted targets for the small demo set: initial indexing ≤5 minutes, ranked search ≤3 seconds, first playable preview ≤5 seconds, with visible queued progress. Targets are not yet measured promises. |
| 19 | Pretrained inference versus training/fine-tuning objective | answered | Fine-tune a small part of the pretrained visual encoder using transition preferences, with a frozen-encoder comparison. Training only a new ranking head over frozen features is not the agreed substitute. |
| 20 | Visual versus motion emphasis; learned versus classical motion | answered | Compare classical and learned motion and choose from evidence. Composition, motion, pose, and secondary semantics retain the priorities in item 4. |
| 21 | Stack preferences and learning objectives | answered | Use React/TypeScript browser UI, Python API and one worker, SQLite, and local files. |
| 22 | Time budget, demo date, essential fallback capabilities | answered | User: “No real deadline just keep client facing benchmarks in mind.” Preserve the agreed functional core and latency targets; milestone sizing follows measured evidence. Fine-tuning is now an important learning deliverable and cannot be silently dropped as an optional extra comparison. |

## D. Quality and completion

| ID | Interview item | Status | Answer, proposal, or remaining detail |
| --- | --- | --- | --- |
| 23 | Success criteria, evaluation collection, useful-suggestion target | answered | Accepted starting gate: 8–10 outgoing queries, at least one user-keepable match among top six for at least half, and three convincing demo exports. Report misses; these targets have not yet been achieved or measured. |
| 24 | User labeling; blind pairwise comparisons or top-k ratings | answered | User can spend ~15–20 minutes on both usefulness ratings and blind pairwise preferences. Separate training and held-out evaluation by source recording. No labels collected yet. |
| 25 | Optional scores, model comparisons, inference-performance display | answered | Include an optional compact explanation/performance panel with component evidence, model versions, timings, and baseline-versus-adapted comparisons. |
| 26 | Local, recorded, or public demo; access by other people | answered | Both a live local demo on this Mac and a recorded walkthrough. No additional remote access requested; footage/inference remain local and no public service will be provisioned. |
| 27 | Deliverable priorities and where to invest polish | answered | Working application and playable demo results first, followed by benchmark/fine-tuning evidence and documentation. All agreed deliverables remain in scope. |

## Additional consequential details to resolve

- Import storage: **answered** in batch 4. Make managed copies; originals remain untouched. Include copies in the 10 GB working footprint and deduplicate repeated imports by content identity.
- Model comparison budget: weight and working-disk caps answered in item 17; benchmark/time scope still depends on items 19–22.
- Real-footage usefulness gate: an empirical result plus user feedback, not synthetic diagnostic success.

## Interview history and next steps

1. Read the brief and companion prompt; inspected workspace instructions, hardware, installed tools, and current primary model documentation.
2. Batch 1 asked items 1–4. User established interests, audience, workflow, and matching priorities; concrete examples remain open.
3. Batch 2 answered items 5, 6, 9 and delegated items 7, 8. User chose normal-speed hard cuts, ranked previews plus a two-clip export, reusable public samples selected by the agent, agent-chosen collection scope, and mostly single-shot clips. Specific desired-cut examples remain open.
4. Batch 3 answered items 10–14: individual-frame controls, two seconds each side plus nearby timing suggestions, padding with optional crop and 1080p MP4, muted audio, six diverse results excluding the outgoing source/duplicates.
5. Batch 4 answered items 15–18 plus import storage: this Mac, fully local inference/footage, $0 services / 2 GB weights / 10 GB storage caps, accepted latency targets with queued progress, managed copies.
6. Batch 5 established fine-tuning as important, agreed classical-versus-learned motion comparison and the React/Python stack, specified no calendar deadline while retaining client-facing benchmarks, and accepted concrete creative targets (item 4).
7. Batch 6 accepted the numeric quality gate, a short user session with both usefulness ratings and blind preferences, the optional explanation/performance panel, and actual adaptation of a small part of the pretrained encoder.
8. Final batch selected both a live local demo and recording, with application/demo results receiving polish first. All 27 items are answered or explicitly delegated.
9. Implementation plan recorded in `docs/poc-plan.md`; proceed with the already-authorized build. User feedback/ratings remain necessary to evaluate aesthetic success and perform the agreed preference-based fine-tuning, not as a routine build approval.

Research hypotheses and primary sources are in [feasibility-research.md](feasibility-research.md). They are not user decisions or measured benchmarks.

## Follow-up — targeted local footage (2026-10-20)

The user added `Videos/` and explicitly authorized using its clips and making the necessary code changes. Eight files were inspected and imported locally as managed copies. They form the default `targeted` collection; original samples are retained in a separate selectable scope. No upload, paid service, training, or new model download was used. Source reuse rights were not inferred from these user-provided files. Added optional rounded-object retrieval and incoming timing refinement; the subjective quality gate still requires feedback on real playback.
