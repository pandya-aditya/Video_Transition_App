# Match Cut local POC plan

Agreed scope: 2026-10-19 (America/Toronto). See [planning-decisions.md](planning-decisions.md) for all 27 answers/delegations. Implementation is authorized; no separate routine approval is required.

## Workflow and scope

Import reusable public clips as managed local copies. Show indexing progress. Scrub an outgoing clip and snap/step to actual source frames. Search other sources; show up to six diverse playable transitions, with duplicate suppression. Default playback is two seconds before/after a normal-speed hard cut, muted. Offer nearby timing suggestions (initial ±0.5 seconds), individual-frame adjustment on both sides, padding or crop-to-fill, and a 1080p H.264 MP4 export. Optional diagnostics explain component evidence and show model/config versions and timings.

Creative focus: sports, film, and recordings of everyday life; composition/shape, motion direction/speed, pose, and secondary semantic connection. Initial targets are jump/reach pose continuity, same-direction movement across sports and film, and similarly positioned rotations. These are experiments, not guaranteed capabilities. Begin with 12–16 mostly single-shot clips, about 2–4 minutes, selected for varied actions and distractors before model rankings. Preserve source families across excerpts/encodes. Add a few sources only if honest train/validation/test separation needs them.

Exclude a full editing timeline, multi-clip montage generation, speed ramps, music/beat alignment, fades, accounts, hosted workers, and public uploads. Fine-tuning a small part of the pretrained visual encoder is required; a frozen-feature ranking head alone is not equivalent.

## Architecture and data flow

React/TypeScript UI → local Python API → SQLite job queue → one Python worker → local originals/proxies/features/previews/exports. Serve only on loopback. Start with SQLite and exact vector search; no broker, remote storage, or vector service.

Import → hash/copy/probe → persist source PTS/time base and frame map → shot guards/proxy/thumbnails → sampled learned appearance/spatial features and temporal descriptors. Search → selected source frame → broad candidate retrieval → validity/source/duplicate filtering → ordered temporal/composition/pose scoring → diverse results → render first preview, then remaining previews on demand. Frame adjustment/export use the same immutable edit specification.

Minimal records: assets and source families; versioned moments/features; jobs; searches/results; edits/exports; labels and evaluation splits. Feature arrays and media live on disk; SQLite records paths, checksums, metadata, and configurations. Rebuild the in-memory exact index from compatible cached features.

Jobs have queued/running/succeeded/failed/cancelled states, bounded progress, attempts, errors, and outputs. Use one worker owner, atomic artifact publication, interrupted-job recovery, and cooperative cancellation. Failed previews/exports must not invalidate indexing. Deduplicate managed imports; clear derived data independently of originals.

## Models and comparison

1. Start with frozen DINOv2 ViT-S/14: approximately 88 MB weights, global features for appearance retrieval and spatial patch pooling for composition. Compare global-only versus composition-union retrieval. Pin weights and processor revisions.
2. Compare Farnebäck classical flow with RAFT Small on the same short windows. Analyze forward motion leading into A and leaving B; never compute flow across the cut itself. Preserve direction and spatial structure, normalize by actual time and frame dimensions, and handle stationary motion explicitly.
3. Evaluate explicit pose landmarks if the approved human-pose examples expose a gap. MediaPipe Pose Landmarker is the compact candidate; license/wheel/coverage checks precede selection. Do not label generic embeddings as measured pose agreement.
4. SigLIP 2 Base is a bounded semantic comparison if needed (combined checkpoint approximately 1.5 GB); it fits the weight cap with the small models but consumes most of it. Add it when retrieval failures justify the comparison rather than downloading it by default.
5. Fine-tune a small subset of DINOv2's final block using real user preferences. Record trainable tensors/count, optimizer, seeds, loss, validation stopping, and changed weights. Keep frozen and adapted representations in separate caches/indexes. Prefer the frozen default if adaptation does not improve held-out results.

Benchmark CPU/MPS on this Mac with pinned dependencies, warmup, synchronization, bounded batches, and separately timed decode/preprocess/inference/retrieval/ranking/rendering. Basic MPS computation is confirmed; model performance is still unknown. Measure fresh and cached runs, memory, disk growth, and repeated latency. Model choice and motion method remain hypotheses until measured.

## Feasibility experiment and milestones

| Milestone | Observable completion |
| --- | --- |
| 1. Sources and media correctness | Approved public-source manifest with attribution/checksums; playable sources; actual PTS map; synthetic CFR/VFR/rotation fixtures; managed-copy and frame-selection checks. |
| 2. Thin inference pipeline | CLI or minimal review page takes an outgoing source frame and produces real retrieved candidates, temporal rankings, component evidence, measured timings, and playable transition files. Compare appearance-only with combined ranking. No fabricated rankings or polished UI dependency. |
| 3. Usefulness review | Inspect real transitions and failure cases; collect a small user review set with usefulness labels and randomized blind pairwise comparisons. Diagnose sampling, retrieval recall, and temporal ranking independently if quality is weak. Improve before broad UI work. |
| 4. Local editing flow | Import/progress/search/diverse previews/frame adjustments/framing/export work end to end, recover across refresh/worker restart, and expose errors/cancellation clearly. Source-frame preview and export boundaries agree. |
| 5. Adaptation and evaluation | User labels separated by source family; actual pretrained weights updated; frozen-versus-adapted comparison on held-out sources; no asserted improvement without evidence. Record motion ablation, failures, resource use, and quality results. |
| 6. Handoff | Reproducible pinned setup, runnable app, three user-approved demo exports if the quality gate passes, benchmark/architecture notes, demo script, recorded walkthrough, and next-experiment roadmap. |

The first technical milestone delivered to the user is the complete thin pipeline in milestone 2. Source/media work is supporting preparation. A compact label/review interface is justified at milestone 3; large UI investment waits for useful playback.

## Evaluation and budgets

Evaluate 8–10 outgoing moments; the agreed starting gate is at least one user-keepable transition among the top six for at least half, plus three convincing demo exports. The user will spend approximately 15–20 minutes on usefulness ratings and blind A/B preferences. Include ties/skip, randomize order, retain both cut points/configs, and distinguish provisional agent inspection from user judgments.

Define train/validation/test by source family before training. Neither side of a held-out pair may appear in tuning; keep adjacent frames, alternative encodes, and excerpts from one recording together. Use a small tuning review first, then reserve untouched sources/queries for final evaluation. Report counts and uncertainty rather than broad statistical claims. Assess useful-candidate presence in retrieval separately from ranking.

Hard caps: $0 services, ≤2 GB downloaded/model checkpoint weights including adapted checkpoints, ≤10 GB local project working footprint including environment/cache/media. Begin with only the small encoder/flow assets. Working engineering limits: one model-heavy worker, bounded frame batches, roughly ≤4 GB worker memory target; measure before increasing. Initial import guardrails: at most 20 clips, 10 minutes total, 500 MB per file, within remaining disk allowance. The smaller demonstration collection is the primary benchmark.

Accepted user-facing targets for the demo set: first indexing ≤5 minutes; ranked search ≤3 seconds after indexing; first playable preview ≤5 seconds. Show queued progress and report misses. Measure training separately; no agreed training-speed claim. Keep caches inside the project, count shared/hardlinked files consistently, and report retained versus temporary download usage.

## Correctness, risks, and fallbacks

- Store integer source PTS with rational time bases; derive UI seconds. Snap scrubbing to decoded frames. Define A's final included frame and B's first included frame explicitly. Preserve original rotation and map proxy timestamps to originals.
- Generate previews and exports from the same edit specification; re-encode for exact source-frame boundaries. Verify decoded boundary content, durations, framing, mute state, and browser playback. A nominal fps calculation or keyframe seek alone is insufficient.
- Version source identity, weights, preprocessing, sampling, and temporal settings separately from ranking weights. Changing only ranking weights must reuse compatible features.
- Global embeddings can favor semantic sameness; union composition candidates before reranking and inspect recall. Camera motion can dominate flow; retain failure examples and test compensation only if justified.
- A small labeled collection can overfit; regularize/limit trainable parameters, use untouched source groups, and retain the baseline when adaptation loses. If the user has not yet supplied labels, expose review tools and report adaptation as pending rather than manufacture preferences.
- If MPS operators fail, explicitly benchmark CPU fallback or a compatible implementation. Reduce analysis resolution, shortlist size, or cache temporal descriptors to meet latency, then check quality again.
- Short clips may lack two-second context; filter invalid moments and show fewer candidates rather than stretching/repeating footage. Missing pose detections are unavailable evidence, not zero similarity or invented landmarks.
- Public source availability may change. Record exact provenance/checksums and use a small reproducible manifest; keep any share-alike output obligations visible in attribution files. No footage uploads.

Meaningful verification covers source timing/VFR/rotation, ordered scoring and stationary flow, source/duplicate/diversity filters, cache/version isolation, job cancellation/recovery, adaptation weight updates/leakage checks, API behavior, and an actually playable export. Synthetic fixtures are clearly labeled and cannot establish aesthetic success.

## Proposed demo sequence

Show the small source collection and completed processing. Select an outgoing sports frame, search, and play the six varied results. Compare one motion-aware suggestion against the appearance baseline. Step a cut by a frame and toggle framing, then export/play the muted 1080p transition. Open diagnostics for real latency and component evidence. Show frozen/adapted comparison only after training/evaluation. End with one documented failure and the next experiment. Record this local workflow alongside the live runnable app.

Priority: working editing flow and playable results first, then evaluation evidence and documentation. No calendar deadline. This plan will be updated from measured evidence without silently changing material user choices.
