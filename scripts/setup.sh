#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
export UV_CACHE_DIR="$PWD/.cache/uv"
uv venv --python 3.11 .venv
uv pip sync --python .venv/bin/python requirements.lock
.venv/bin/python scripts/download_models.py
(cd web && npm ci --cache ../.cache/npm --no-audit --no-fund && npm run build)
printf '\nSetup complete. Optional public demo: .venv/bin/python scripts/fetch_samples.py\nThen: .venv/bin/python -m matchcut.cli samples\nRun: ./scripts/run.sh\n'
