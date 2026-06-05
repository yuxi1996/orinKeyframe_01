#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -d "datasets/xlebench_partial/Ego4D/v2/full_scale" ]; then
  python3 run_benchmark.py --video_dir "datasets/xlebench_partial/Ego4D/v2/full_scale" --config config/xlebench.yaml
else
  python3 run_benchmark.py --video_dir videos
fi
