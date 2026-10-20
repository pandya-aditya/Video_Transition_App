# Match Cut

A local creative experiment: choose an outgoing video frame, retrieve possible next shots with pretrained DINOv2, rank their composition/motion/pose continuity, and preview or export a hard cut. React/TypeScript + FastAPI, SQLite, one worker. No hosted inference or footage uploads.

## Run

On the development Mac, the environment and sample data are already local:

```sh
./scripts/run.sh
```

Open **http://127.0.0.1:8765**. Import video or select a sample. Choose an outgoing frame with at least two seconds before it, click **Find the next shot**, select a match, adjust either source frame, and build a preview or export a muted 1080p MP4. A frame number is a decoded source-frame index, starting at zero. The outgoing frame is included; the incoming frame is the first frame after the cut.

Fresh setup requires Python 3.11, `uv`, Node and npm:

```sh
./scripts/setup.sh
.venv/bin/python scripts/fetch_samples.py
.venv/bin/python -m matchcut.cli samples
./scripts/run.sh
```

Model setup downloads approximately 98 MB of pretrained weights. Dependencies and weights are pinned in `requirements.lock`, `web/package-lock.json`, and `models.lock.json`. Setup needs internet; the running app loads models from disk. Model downloads are explicit and never triggered by a search. Public hosts may rate-limit sample downloads; completed files and provenance are retained. No paid services are used.

## Experiment and review

```sh
.venv/bin/python -m matchcut.cli search
.venv/bin/python -m matchcut.cli motion-benchmark
PYTHONPATH=. .venv/bin/python scripts/prepare_review.py
.venv/bin/python -m pytest -q
cd web && npm run build
```

The CLI writes actual retrieved results and playable previews to `data/experiment.json` and `data/artifacts/`. Synthetic videos exist only in tests. The app collects useful/not-useful labels and a prepared blind A/B study. No user labels or perceptual success scores are fabricated.

Fine-tuning updates normalization weights in the last pretrained DINOv2 transformer block. It requires at least six decisive training preferences and two validation preferences from disjoint source families. Run only after the review:

```sh
.venv/bin/python -c 'from matchcut.adaptation import fine_tune; print(fine_tune())'
```

The experimental checkpoint and report live in `data/models/adapted-normalization.pt` and `data/adaptation-report.json`. The frozen encoder remains the app default until held-out evaluation justifies promotion. A changed checkpoint is not evidence of improved match quality.

## Scope and limits

- Defaults: 2 seconds on each side, 30 fps preview/export, padding or crop, no audio. Source PTS and time base are retained. Boundary source frames are explicitly retained during CFR resampling; other frames may be dropped/repeated for mixed frame rates.
- Source families are excluded from matching. Public samples from the same event are grouped conservatively. User imports currently default to their file hash as family; related excerpts need grouping in metadata before a valid evaluation.
- Models can confuse background similarity with creative continuity. Pose may miss small, occluded, or unusual bodies. Optical flow includes camera motion. Scores are heuristics, not probabilities.
- Shot detection is a conservative pixel-change guard; subtle cuts/dissolves can escape it. Inspect previews.
- Local limits: 20 assets, 10 minutes, 500 MB/file, 10 GB working footprint. This is a POC, not a hardened untrusted-media service. Bind only to loopback.
- Fine-tuning, the subjective quality gate, and three approved demo cuts require your actual review. Current limitations and measured timings belong in `docs/benchmark-report.md`.

See [planning decisions](docs/planning-decisions.md), [implementation plan](docs/poc-plan.md), [model research](docs/feasibility-research.md), [architecture](docs/architecture.md), and [demo script](docs/demo-script.md). Exact footage source, author, license and checksum are in `samples-manifest.json`; retain attribution and applicable share-alike terms when sharing adapted exports.
