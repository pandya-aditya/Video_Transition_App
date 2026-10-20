# Initial feasibility findings — 2026-10-20

This is an engineering feasibility report, not a passed creative-quality evaluation. The user inspected the app and reported that transitions were not great. No human labels have been fabricated and no encoder has been fine-tuned yet.

## Measured local run

Hardware: M2 MacBook Air, 16 GB. DINOv2 inference on MPS, BlazePose Lite CPU, PyTorch 2.5.1. Ten actual public clips, 174.45 seconds, nine conservatively grouped source families. Raw outputs: `data/benchmark.json`, `data/motion-benchmark.json`; version identifiers are inside those files.

- Sum of recorded feature-index times: 186.64 seconds. This excludes downloads, import/probe, initial font-cache generation and model startup; it is **not** an end-to-end five-minute indexing pass.
- Nine valid outgoing queries, with warm model: combined search 0.63–2.70 seconds.
- Uncached 360p previews: 1.86–3.24 seconds. Queue and browser polling add overhead.
- A separate first browser search took 3.74 seconds and missed the three-second target. Cold startup remains a distinct limitation.
- Working footprint at benchmark: 2.25 GB (deduplicated by inode), within the 10 GB cap. Model weights are well below 2 GB.
- Five identical motion windows, two runs per method: second-run median including decode was 0.266 s Farnebäck and 0.372 s RAFT Small. This is a tiny latency comparison, **not** evidence that either flow method yields better transitions.

The first earlier pipeline had a 3.98 s cold search and a 6.11 s preview. Bounded decode resolution reduced preview costs. The current renderer and preprocessing are versioned separately from earlier artifacts.

## Quality findings

The appearance-plus-motion first trial paired a standing basketball shooter with a gymnast on the floor: background/semantic and broad movement similarities did not establish a satisfying body match. Explicit pose was added in response. The combined method still retained the appearance-only top result in 6 of 9 benchmark queries. Rank changes alone do not establish improvement. Pose is absent in many candidates, particularly distant/inverted/occluded people.

The collection was useful for exercising the pipeline but was selected chiefly for accessible licensing and variety. It is not established to contain enough satisfying transitions. Half-second sampling can miss the decisive incoming action phase. Four spatial mean-flow vectors discard much of limb articulation; camera motion remains a confound. Current global/spatial visual features can favor setting over subject.

## Next experiment, before broad refactoring or tuning

1. Establish 6–10 human-recognizable positive edits across 2–3 action patterns: reach/jump, turn/spin, and lateral movement. Add deliberately complementary footage within the local budget, rather than indiscriminate volume. Keep source provenance and family separation.
2. Measure whether the known incoming moments appear anywhere in retrieval. If absent, fix sampling/representation/recall. If present but buried, fix ranking. If no satisfying edit exists even manually, change the footage.
3. Compare full-frame against subject-focused representations and screen-space subject position/scale. Refine incoming cut points around retrieved moments. Compare short motion trajectories and action phase, not just one mean flow pair.
4. Collect usefulness labels, reason tags and about 30–50 blind preferences on credible candidates. Then adapt the small encoder subset and evaluate on untouched source families. Minimum labels enforced by the trainer are a smoke-test threshold, not a claim of sufficient data.
5. Refactor only to isolate retrieval, temporal ranking, and evaluation variants. More infrastructure or visual polish does not address the demonstrated failure.

The agreed gate remains pending: a user-keepable top-six result for at least half of 8–10 moments and three convincing user-approved exports. A blind review set of 25 actual pairs is prepared, but collecting preferences on uniformly weak options should not substitute for the positive-edit feasibility experiment.
