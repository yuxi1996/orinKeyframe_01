#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${PROJECT_ROOT}"

VENV_DIR=".venv"
PYTHON_BIN="python3"
VIDEO_DIR="datasets/xlebench_partial/Ego4D/v2/full_scale"
ORDER_MODE="manifest"
RUN_DOWNLOAD=1
RUN_BENCHMARK=1
RUN_TEGRSTATS=1
DRY_RUN_DOWNLOAD=0
INSTALL_YOLO=0
AWS_CONFIG_PATH=""
AWS_CREDENTIALS_PATH=""
AWS_PROFILE_NAME=""

usage() {
  cat <<'EOF'
Usage:
  bash scripts/orin_auto_setup_download_test.sh [options]

Options:
  --venv DIR              Virtualenv directory. Default: .venv
  --python BIN            Python executable. Default: python3
  --skip-download         Do not download Ego4D videos.
  --skip-benchmark        Do not run benchmark after setup/download.
  --dry-run-download      Print Ego4D video IDs and command, but do not download.
  --order-mode MODE       manifest, symlink, or copy. Default: manifest
  --install-yolo          Install ultralytics in the venv. YOLO still needs weights/yolo26n.pt.
  --no-tegrastats         Do not start tegrastats monitor during benchmark.
  --aws-config PATH       Ego4D/AWS config path. Not stored in this repo.
  --aws-credentials PATH  Ego4D/AWS credentials path. Not stored in this repo.
  --aws-profile NAME      AWS profile name. Optional.
  -h, --help              Show help.

Default flow:
  1. Create venv with --system-site-packages so Orin system OpenCV remains usable.
  2. Install portable Python dependencies and ego4d CLI.
  3. Run scripts/check_env.py.
  4. Download X-Lebench Ego4D full_scale videos.
  5. Generate ordered manifest.
  6. Run benchmark with config/xlebench.yaml.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --venv)
      VENV_DIR="$2"
      shift 2
      ;;
    --python)
      PYTHON_BIN="$2"
      shift 2
      ;;
    --skip-download)
      RUN_DOWNLOAD=0
      shift
      ;;
    --skip-benchmark)
      RUN_BENCHMARK=0
      shift
      ;;
    --dry-run-download)
      DRY_RUN_DOWNLOAD=1
      shift
      ;;
    --order-mode)
      ORDER_MODE="$2"
      shift 2
      ;;
    --install-yolo)
      INSTALL_YOLO=1
      shift
      ;;
    --no-tegrastats)
      RUN_TEGRSTATS=0
      shift
      ;;
    --aws-config)
      AWS_CONFIG_PATH="$2"
      shift 2
      ;;
    --aws-credentials)
      AWS_CREDENTIALS_PATH="$2"
      shift 2
      ;;
    --aws-profile)
      AWS_PROFILE_NAME="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

mkdir -p outputs/logs
LOG_FILE="outputs/logs/orin_auto_setup_download_test.log"
exec > >(tee -a "${LOG_FILE}") 2>&1

echo "========== Orin auto setup/download/test =========="
date
echo "Project root: ${PROJECT_ROOT}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Python not found: ${PYTHON_BIN}"
  exit 1
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "[1/7] Create venv with system site packages: ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv --system-site-packages "${VENV_DIR}"
else
  echo "[1/7] Reuse venv: ${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade "pip<26" "setuptools<82" wheel

echo "[2/7] Install runtime dependencies"
python -m pip install numpy psutil PyYAML ego4d
if [[ "${INSTALL_YOLO}" -eq 1 ]]; then
  python -m pip install ultralytics
else
  echo "Skip ultralytics install. Use --install-yolo if YOLO is needed."
fi

echo "[3/7] Environment check"
python scripts/check_env.py | tee outputs/logs/check_env.json

echo "[4/7] Ego4D download"
DOWNLOAD_CMD=(python scripts/download_xlebench_ego4d.py)
if [[ -n "${AWS_CONFIG_PATH}" ]]; then
  DOWNLOAD_CMD+=(--aws_config "${AWS_CONFIG_PATH}")
fi
if [[ -n "${AWS_CREDENTIALS_PATH}" ]]; then
  DOWNLOAD_CMD+=(--aws_credentials "${AWS_CREDENTIALS_PATH}")
fi
if [[ -n "${AWS_PROFILE_NAME}" ]]; then
  DOWNLOAD_CMD+=(--aws_profile "${AWS_PROFILE_NAME}")
fi
if [[ "${DRY_RUN_DOWNLOAD}" -eq 1 ]]; then
  DOWNLOAD_CMD+=(--dry_run)
fi

if [[ "${RUN_DOWNLOAD}" -eq 1 ]]; then
  "${DOWNLOAD_CMD[@]}"
else
  echo "Download skipped by --skip-download."
fi

echo "[5/7] Prepare ordered video manifest"
python scripts/prepare_xlebench_order.py --mode "${ORDER_MODE}" --video_dir "${VIDEO_DIR}"

echo "[6/7] Benchmark"
TEGRSTATS_PID=""
cleanup() {
  if [[ -n "${TEGRSTATS_PID}" ]]; then
    kill "${TEGRSTATS_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

if [[ "${RUN_BENCHMARK}" -eq 1 ]]; then
  if [[ "${RUN_TEGRSTATS}" -eq 1 ]] && command -v tegrastats >/dev/null 2>&1; then
    echo "Start tegrastats monitor: outputs/logs/tegrastats.log"
    tegrastats --interval 1000 --logfile outputs/logs/tegrastats.log &
    TEGRSTATS_PID="$!"
    sleep 1
  else
    echo "tegrastats monitor disabled or unavailable; GPU/power fields may be N/A."
  fi

  if compgen -G "${VIDEO_DIR}/*.mp4" >/dev/null; then
    python run_benchmark.py --video_dir "${VIDEO_DIR}" --config config/xlebench.yaml
  else
    echo "No downloaded mp4 files found in ${VIDEO_DIR}."
    echo "Run download first, or check Ego4D credentials/access."
    python run_benchmark.py --video_dir "${VIDEO_DIR}" --config config/xlebench.yaml
  fi
else
  echo "Benchmark skipped by --skip-benchmark."
fi

echo "[7/7] Done"
cat <<EOF
Outputs:
  ${PROJECT_ROOT}/outputs/logs/orin_auto_setup_download_test.log
  ${PROJECT_ROOT}/outputs/logs/check_env.json
  ${PROJECT_ROOT}/outputs/json/benchmark_summary.json
  ${PROJECT_ROOT}/outputs/reports/benchmark_report.html
EOF
