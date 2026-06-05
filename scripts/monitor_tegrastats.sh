#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p outputs/logs
if command -v tegrastats >/dev/null 2>&1; then
  tegrastats --interval 1000 --logfile outputs/logs/tegrastats.log
else
  echo "tegrastats not found; GPU and power metrics will be N/A."
fi
