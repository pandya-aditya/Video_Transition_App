# Match Cut — proof-of-concept design brief

## Purpose and handoff

This document gives a coding agent enough context to interview the user, investigate feasibility, propose a concrete plan, and build a proof of concept. It is a starting hypothesis, not an approved technical specification. Use the companion `MATCH_CUT_POC_PROMPT.md` as the initiating prompt.

The workspace happens to be named Basketball Inference. This does not establish the product name or restrict the footage to basketball. Do not rename or relocate it without discussing that with the user.

## User intent

Build a personal, creative project that discovers visually satisfying transitions between videos. The user wants a passion project, with ML inference central to the experience, rather than a generic business application or an application built merely to match job descriptions.

The eventual project should be end-to-end, visually compelling in a demo, inexpensive to operate, rich in documentation and systems-design decisions, and possible to start without third-party permissions or lengthy integration setup. A polished, credible inference pipeline matters more than a long feature list.

Examples of the creative intent:

- A rotating basketball cuts to a rotating wheel.
- A person jumping cuts to a game character landing.
- Two different scenes connect through subject position, shape, movement, or composition.

These are aspirational examples, not established model capabilities or guaranteed POC outcomes.

## Core hypothesis

A useful system can retrieve broadly compatible visual moments cheaply, then rank a small candidate set using temporal and compositional evidence. A user can preview the actual transitions and adjust the cut points.

Visual similarity is not equivalent to a good cut. Semantic embeddings may retrieve the same kind of object while missing an aesthetically stronger match involving a different object. Motion compatibility is directional: A → B and B → A can have different quality.

The POC must test whether suggestions are creatively useful before investing in production infrastructure.

## Planning interview — ask all of these

Ask these questions conversationally in small batches as the plan develops. They include the unresolved product, inference, media, evaluation, and operational decisions from the architecture discussion. Do not present the entire questionnaire in one message.

First inspect what can safely be learned from the workspace and hardware. Do not ask the user to manually provide facts already available. Present observed facts for confirmation where relevant. For preference questions, offer a recommendation and explain its tradeoff. Let the user delegate choices. Record every question's disposition: answered, delegated, or unresolved. Do not silently treat a proposed default as a user decision.

### A. Creative purpose and first experience

1. What footage would you enjoy using: sports, gaming, travel, films, your own recordings, or something else? Which specific interests should shape the project?
2. Are you primarily making a tool for your own edits, or a demo other people should be able to try?
3. Should the first workflow be selecting one outgoing moment and finding its next shot, or automatically discovering pairs anywhere in a folder? Suggested starting point: selected-moment search.
4. What makes a transition satisfying to you: composition/shape, motion direction and speed, pose, color, semantic connection, deliberate contrast, or a combination? Can you provide or describe a few examples?
5. Should the first output use normal-speed hard cuts, or do speed changes, beat alignment, crossfades, or other effects need to be part of the POC? Suggested starting point: hard cuts.
6. What is the desired result: ranked previews, one downloadable two-clip transition, or a multi-clip sequence? Suggested starting point: ranked previews plus a two-clip export.

### B. Footage, timing, and controls

7. Do you already have sample footage? What may the agent use, and where is it? If it is unavailable, should the agent use user-approved reusable samples or generated diagnostic fixtures? Do not search unrelated personal folders.
8. Roughly how many videos, how many total minutes, and what resolutions/frame rates should the POC handle? Are mixed portrait/landscape clips important?
9. Will the source videos be single shots, edited videos with multiple shots, gameplay recordings, or a mixture? This determines whether shot-boundary handling is essential immediately.
10. How should users choose and refine a cut: scrub to a timestamp, mark a range, or accept automatically chosen moments? Is frame-accurate trimming necessary in the first demo?
11. How much context should play before and after each cut? Should the system suggest small timing adjustments as well as the matching video?
12. How should differing aspect ratios be handled: preserve with padding, crop, or user selection? What export resolution/format is needed?
13. Should the POC preserve source audio, mute it, or support a music track? Audio processing and beat matching are separate scope decisions.
14. Should matches exclude the same source video and near-duplicate moments? How diverse should the result list be?

### C. Inference and operational constraints

15. Confirm the available development/demo hardware after inspection, including memory and GPU/accelerator availability. Must the demo run on this same machine?
16. Must processing stay local, or is a hosted worker acceptable? May video leave the machine? Suggested starting point: local processing and a browser UI.
17. What is the spending cap for the POC, including any model APIs, compute, and hosting? Are model downloads acceptable? No paid service is implied by this brief.
18. What is acceptable for initial indexing time and subsequent search latency? Is a queued wait acceptable, or should the experience feel nearly immediate?
19. Is the user comfortable starting with pretrained models, or is training/fine-tuning itself a desired project objective? Suggested starting point: pretrained inference and measured comparisons.
20. Should the initial emphasis be visual/compositional matching, motion matching, or both? Is learned motion inference important, or is classical optical flow acceptable as a baseline alongside a learned visual encoder?
21. Are there stack preferences or technologies the user wants to learn? Suggested starting point: React/TypeScript UI, Python API/worker, SQLite, local artifact storage.
22. What time budget or target demo date should shape the plan? Which capabilities are essential if the inference experiment is harder than expected?

### D. Quality and completion

23. What would make the user consider the POC successful after trying it? Agree on a small evaluation collection and a realistic number of useful suggestions rather than inventing a target score.
24. Can the user label a small set of preferred and rejected transition pairs? Should comparisons be blind pairwise preferences, top-k usefulness ratings, or both?
25. Should the UI expose component scores, model comparisons, and inference performance? Suggested starting point: a compact optional debug panel.
26. Is the final demo local, recorded, or publicly hosted? Does anyone besides the user need access? Public hosting changes upload, authentication, cost, and cleanup requirements.
27. When the POC is finished, which deliverables matter most: working application, demo footage, benchmark report, architecture documentation, or a roadmap? Which should receive polish first?

After the interview, summarize the chosen workflow, constraints, success criteria, and deferred scope. Ask follow-up questions only for consequential gaps. Do not ask the user to choose routine implementation details that the agent can evaluate.

## Proposed POC boundary — subject to the interview

One user imports a small collection of videos, selects an outgoing cut timestamp, searches across other moments, previews ranked transitions, adjusts timing, and exports one two-clip sequence.

Include actual learned visual inference and explicit temporal analysis. The choice of motion method is open. Do not substitute fabricated embeddings, random rankings, or manually curated results for inference. Clearly label synthetic fixtures and precomputed demo results.

Initially defer a full nonlinear video editor, multi-user collaboration, online accounts, music licensing integrations, foundation-model training, generated in-between frames, and a distributed deployment. Revisit these only if the user prioritizes them.

## Logical architecture

```text
Video import
  → inspect media and register source
  → background jobs create preview media and sample candidate moments
  → visual inference and reusable feature extraction
  → feature store + searchable index

Selected outgoing cut
  → retrieve broad candidate set
  → filter invalid / duplicate candidates
  → analyze outgoing and incoming windows
  → rank + diversify
  → preview / adjust cut points
  → export from original media
```

Keep these as logical boundaries, not automatically separate services. A frontend, API process, and background worker are sufficient initially. A worker can poll durable database jobs; introduce a broker only if justified.

### Responsibilities

| Component | Responsibilities |
|---|---|
| Frontend | Import, progress, source browsing, timestamp selection, previews, trimming, export requests |
| API | Validate requests, manage projects and metadata, submit jobs, expose search and artifact access |
| Worker | Probe/decode media, generate proxies, run models, compute features, rank candidates, render exports |
| Metadata store | Source identity, moment locations, feature versions, job state, selections, evaluations |
| Artifact storage | Originals or explicit source references, proxies, thumbnails, feature arrays, preview/export files |
| Search index | Rebuildable retrieval structure derived from versioned features |

Do not run long processing operations inside an HTTP request. Browser refreshes should not destroy completed processing.

## Media representation and correctness

- Preserve originals. Determine whether imports copy files or reference them; explain disk usage and missing-source behavior.
- Store presentation timestamps and their time bases, plus convenient normalized seconds. Account for variable frame rates, rotation metadata, and differing aspect ratios.
- Represent a candidate cut as a source timestamp and a surrounding temporal window, not just a still frame.
- Sample coarsely for retrieval and refine timing around shortlisted candidates. Measure the quality/cost tradeoff rather than fixing an arbitrary universal frame rate.
- Keep candidate windows inside a shot or explicitly handle shot boundaries. Exclude windows without sufficient pre/post-roll.
- Track the mapping between preview media and original timestamps. Preview and export must select equivalent content.
- Re-encoding may be needed for frame-accurate cuts; do not assume arbitrary stream-copy boundaries are exact.

## Inference and ranking design

Begin by benchmarking a small number of appropriate visual encoders on representative footage and actual hardware. Verify current model APIs, weight licenses, preprocessing requirements, and hardware compatibility from primary sources. Do not select a model solely because its embeddings are popular.

Separate the following concerns:

1. **Retrieval:** broad recall using inexpensive reusable visual representations. Start with exact vector search if the collection is small.
2. **Temporal reranking:** examine footage leading into A and leaving B; compare motion direction, magnitude, composition, and continuity. Document the coordinate system and any normalization.
3. **Diversification:** suppress nearby timestamps, repeated clips, and trivial duplicate matches as appropriate.

Camera motion and subject motion can conflict. Acknowledge this in the initial implementation and include failure examples; add segmentation or camera-motion compensation only when evidence supports it.

Keep component scores separate. Treat an initial weighted combination as a heuristic, not a calibrated probability. Normalize features/scores appropriately; cosine similarity and optical-flow magnitude cannot simply be added without consideration. Explain why a match was suggested without claiming causal certainty.

If visual retrieval misses cross-object matches, experiment with a union of candidates from composition or motion retrieval. Reranking cannot recover candidates that were never retrieved.

Load models once per worker where practical, batch within a memory budget, use appropriate inference/evaluation settings, and support the available device. Measure decode, preprocessing, model execution, retrieval, ranking, and rendering independently.

## Suggested data entities

- **Project:** scope of a footage collection and user settings.
- **VideoAsset:** source identity/hash, location, duration, dimensions, rotation, stream metadata, import status.
- **Moment:** asset ID, source timestamp, temporal bounds, optional shot ID, thumbnail reference.
- **FeatureArtifact:** moment/window identity, encoder and weight version, preprocessing/configuration version, output reference.
- **ProcessingJob:** type, inputs/configuration key, status, progress, attempt count, error, output references.
- **SearchRun:** selected outgoing moment, eligible collection, retrieval/ranking configurations, results and timing.
- **MatchCandidate:** ordered A/B cut points, individual scores, final rank, preview reference, validity information.
- **EditSelection:** chosen pair, trims, framing/audio settings, export status/reference.
- **EvaluationLabel:** pair/settings, preference or usefulness judgment, notes, evaluation-set membership.

Keep the schema small in implementation; these are responsibilities, not a demand for one table per entity.

## Reproducibility, recovery, and costs

Cache artifacts using source identity, temporal selection, model version, and preprocessing configuration. A ranking-weight change should not trigger video re-encoding or embedding regeneration. Incompatible embedding versions must not silently share an index.

Use resumable units of work, bounded frame queues, bounded inference batches, and idempotent artifact publication. Handle corrupt media, worker interruption, cancellation, and partial progress visibly. A failed export should not invalidate successful indexing.

Record storage growth and provide a straightforward way to clear derived artifacts without deleting originals. Set workload limits appropriate to the chosen demo hardware. Do not provision paid infrastructure or expose a public upload endpoint without explicit authorization.

## Evaluation and feasibility gate

Before committing to a large UI build, implement a thin experiment:

`selected timestamp → real visual retrieval → temporal ranking → playable top candidates`

Use varied real footage approved by the user. Synthetic clips are useful for timing, direction, and recovery tests, but do not establish aesthetic usefulness on real footage.

Compare at least a simple appearance baseline with the proposed combined ranking. Evaluate:

- Retrieval: are labeled useful candidates present in the retrieved set?
- Ranking: do users prefer the higher-ranked suggestions and does temporal ranking help?
- Actual playback: do the transitions work at the proposed cut points?
- Performance: import throughput, search latency, model latency, memory, artifact size, and preview/export time.

Avoid evaluation leakage through adjacent frames or alternate encodes of the same footage. Separate tuning and evaluation by source video where possible. Small subjective datasets do not justify broad claims of general quality.

Report real measurements, hardware, dataset size, and failures. If the pipeline is not useful, investigate representation, sampling, retrieval recall, and ranking separately before adding infrastructure or more models.

## Deliverables and definition of done

Finalize numeric budgets and subjective success criteria with the user during planning. At minimum, a successful POC handoff should include:

1. A runnable end-to-end import/search/preview/export flow with genuine inference.
2. Reproducible setup instructions, pinned dependencies, and documented model setup.
3. A small evaluation report comparing approaches, with measured performance and honest limitations.
4. Appropriate verification of timestamp mapping, candidate filtering, cache/version behavior, job recovery, and playable export output.
5. A short demo script using approved footage, including one failure or limitation where useful.
6. Architecture and decision notes explaining what was chosen, what was learned, and what should come next.

Do not fabricate benchmark numbers, declare success from screenshots alone, or claim that subjective match quality has been solved.

## Reference starting points

These inform architectural choices; verify current details when implementing.

- Faiss: https://faiss.ai/
- PyAV media timing: https://pyav.org/docs/stable/api/time.html
- PyTorch inference mode: https://docs.pytorch.org/docs/stable/generated/torch.autograd.grad_mode.inference_mode.html

