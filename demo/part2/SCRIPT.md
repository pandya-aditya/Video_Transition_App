# Part 2 script: architecture, designed for production (about 5 minutes)

Use this with [slides.html](slides.html). Open it in Chrome at full screen (press `F`). Press the right arrow or space at every **[click]**. To see these notes on a second screen, press `P`. That opens a synced presenter window. Press `N` to show the notes and a slide/step counter on the same screen, and press `N` again to hide them before you record. You can deep-link to any build: `slides.html#5.2` opens slide 5 at step 2.

Notation used below:

- **[click]** means advance one build step.
- *Italics* are on-screen cues, not narration.
- Numbers marked "measured" come from `docs/benchmark-report.md` or `demo/part1/captures/results.json`.
- Numbers marked "target" or "estimate" are design assumptions. Say them that way on camera.

---

## Slide 1: From a laptop prototype to a production service (0:00–0:15)

"In the first part you saw Match Cut find a pupil-to-eclipse cut. Now I'll walk through how it works, and how I'd run it as a production service. The prototype runs on my laptop, but I designed it around the seams that a scaled system needs."

## Slide 2: Requirements and scale targets (0:15–0:45)

"First, what production means here.

**[click]** Functionally: many users upload footage, search any frame, and export a frame-exact cut.

**[click]** Non-functionally, I'm designing for these targets. Searches should return in under a second at p95. Indexing should keep pace with uploads, roughly ten thousand hours of footage across tenants. And each tenant's media stays isolated.

**[click]** The hard constraint is correctness. A cut has to land on one exact decoded frame, so the system can't approximate frames from timestamps."

## Slide 3: The core pipeline (0:45–1:10)

"Every version of this system, prototype or production, runs the same five stages.

**[click]** Ingest decodes the video and records every frame's real presentation timestamp.

**[click]** Index samples a frame every half second. It computes DINOv2 embeddings for appearance and composition, optical flow for motion, BlazePose for body pose, and a geometric descriptor for shapes.

**[click]** Search retrieves and ranks the next shots.

**[click]** Render builds a frame-exact MP4.

**[click]** Learn turns user feedback into model improvements.

The key split is that indexing is heavy and runs offline. Search is light and runs online."

## Slide 4: The prototype today, and the seams (1:10–1:45)

"Here's the prototype. React talks to one FastAPI process. SQLite stores assets, jobs and labels. A single worker thread runs every heavy job, and features live on disk as files.

**[click]** That sounds small, but each piece was chosen to map onto a production component.

- The jobs table is already durable, and interrupted jobs return to the queue. That's queue semantics.
- Features are keyed by a hash of the source video plus a hash of the model and preprocessing, so they can move straight into object storage.
- Every render is an immutable edit spec, which makes renders cacheable and idempotent.

**[click]** The one piece that doesn't scale is search. Today it compares the query against every sampled frame of every clip. That's linear, so it's the first thing production replaces."

## Slide 5: Production architecture (1:45–2:35)

"Here's the production design, built up layer by layer.

**[click]** At the edge, the React app is served from a CDN. An API gateway handles authentication and rate limits, and stateless API replicas scale horizontally behind it.

**[click]** For state, Postgres holds metadata, jobs, labels and edit specs, all scoped by tenant. Object storage holds originals, feature files and renders. The client uploads directly to storage through presigned multipart URLs, so large videos never pass through the API.

**[click]** Heavy work goes through a durable queue to separate worker pools. Decoding and rendering run on CPU. Embedding runs on GPUs with dynamic batching. Each pool autoscales on its own queue depth.

**[click]** The interactive path is a dedicated search service. It queries an approximate-nearest-neighbor vector index, then fetches full features from the feature store to rerank.

**[click]** A model registry pins the exact encoder version that every worker loads, which is what makes the features reproducible."

## Slide 6: Ingest and indexing at scale (2:35–3:10)

"Indexing is the throughput problem.

**[click]** An upload creates a content-addressed asset. Identical files are deduplicated by their SHA-256 hash, so the same clip is never indexed twice.

**[click]** Ingest splits each video into shots, and shots fan out as independent jobs. One long video can be spread across many GPUs.

**[click]** Here's the sizing math. Each sample stores about 1,900 floats, roughly 7.7 kilobytes. An hour of footage is 7,200 samples, about 55 megabytes. Ten thousand hours is around 550 gigabytes of full vectors. Those live in object storage. Only compressed vectors need to sit in memory for the ANN index. Product-quantized to 64 bytes each, that's about 5 gigabytes for the global index and about 10 with the spatial index added.

**[click]** On my laptop, measured indexing takes about 1.07 seconds of compute per second of footage. Because jobs are independent, throughput scales linearly with GPU workers, so capacity planning is just division."

## Slide 7: The search path (3:10–3:45)

"Search is a funnel.

**[click]** Start with every sampled frame in the tenant's library, potentially tens of millions.

**[click]** ANN recall pulls a few hundred neighbors each from the global and spatial indexes. It filters by tenant and excludes the query's own source.

**[click]** Reranking applies the expensive signals, motion, pose and shape, but only to that shortlist. So the cost depends on the shortlist size, not the library size.

**[click]** Diversification keeps one result per source family, and you get the top six.

**[click]** Optional timing refinement runs asynchronously and updates the results in place. On the right is the target latency budget that keeps p95 under a second."

## Slide 8: Ranking and the appearance baseline (3:45–4:15)

"The default score blends 35 percent appearance, 40 percent spatial composition and 25 percent motion. When pose is detected, that blend counts for 70 percent and pose for 30.

**[click]** The demo used the appearance baseline: pure DINOv2 similarity. For the eye, it ranked the solar eclipse first at 0.31, and the marbles second.

**[click]** The baseline exists so every ranking change is measured against something. In production, ranking versions are config, not code. So I can A/B test them on live traffic and report how often a keepable cut lands in the top six."

## Slide 9: Rendering at scale (4:15–4:35)

"A render is defined by an immutable edit spec: the two source frames, the durations, the framing and the renderer version.

**[click]** Hashing that spec gives a cache key, so a repeated render is just a CDN hit.

**[click]** Previews and exports run on separate priority queues, so an export never blocks someone's interactive preview. FFmpeg runs in a sandbox, because uploaded media is untrusted input.

**[click]** Correctness is tested. The tests decode the output and compare the boundary pixels to the original source frames."

## Slide 10: Versioning and the learning loop (4:35–5:00)

"Every feature's key includes the model version. That makes model upgrades safe.

**[click]** Users label cuts as keep or pass, and blind A/B pairs give pairwise preferences.

**[click]** Training fine-tunes only the final block's normalization weights, split by source family so validation never sees training footage.

**[click]** A new model goes through shadow evaluation, then backfills a parallel index, blue-green. Traffic flips only when it beats the baseline. The old index stays in place for instant rollback."

## Slide 11: Reliability, security, observability, cost (5:00–5:25)

"**[click]** For reliability, jobs are idempotent and keyed by content. Workers hold leases, failures retry, and poison jobs land in a dead-letter queue. All writes are atomic.

**[click]** For security: OIDC authentication, tenant isolation through row-level security and per-tenant index partitions, and sandboxed decoders.

**[click]** For observability, traces cover every job stage. Service-level objectives track search p95, indexing lag and render time.

**[click]** For cost, workers autoscale on queue depth, backfills run on spot GPUs, and previews render at 360p while exports render at 1080p."

## Slide 12: Tradeoffs and what I'd build first (5:25–5:50)

"To be clear about where this stands: the prototype is a single-machine proof of concept, and its scores are heuristics, not probabilities.

**[click]** If I took it to production, I'd build in this order: the ANN index first, then the queue and worker pools, then multi-tenancy, then the learning loop.

**[click]** The pipeline, the versioning and the correctness tests carry over unchanged. That was the point of designing the seams up front. Thanks for watching."

---

## Delivery notes

- Keep the eye example consistent with Part 1. If you regenerate captures, update the score in Slide 8 from `results.json`.
- Say "target" or "estimate" for any design number that wasn't measured. Interviewers will ask, and this shows you know the difference.
- If you need a 3-minute cut, drop Slides 9 and 11. Their content stays in the presenter notes.
- Likely interview questions:
  - "Why not a vector DB today?" A few hundred thousand vectors are an exact matrix multiply on a laptop. The index is the scaling seam.
  - "Why freeze the encoder?" Labels are scarce, so I only tune a tiny parameter set, and only promote a model on held-out evidence.
  - "What breaks first at scale?" The linear search and the single worker, in that order.
