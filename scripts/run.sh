#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
export HF_HUB_OFFLINE=1
export MPLCONFIGDIR="$PWD/data/matplotlib"
exec .venv/bin/python -m uvicorn matchcut.api:app --host 127.0.0.1 --port 8765
