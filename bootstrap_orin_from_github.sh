#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/yuxi1996/orinKeyframe_01.git"
BRANCH="main"
DEST_DIR="${HOME}/orinKeyframe_01"

usage() {
  cat <<'EOF'
Usage:
  bash bootstrap_orin_from_github.sh [options] [-- extra inner-script options]

Options:
  --repo-url URL      GitHub repository URL.
  --branch NAME      Branch to clone or pull. Default: main
  --dest DIR         Destination directory. Default: ~/orinKeyframe_01
  -h, --help         Show this help.

Common examples:
  bash bootstrap_orin_from_github.sh
  bash bootstrap_orin_from_github.sh -- --dry-run-download
  bash bootstrap_orin_from_github.sh -- --aws-config /path/config --aws-credentials /path/credentials
  bash bootstrap_orin_from_github.sh -- --skip-download
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-url)
      REPO_URL="$2"
      shift 2
      ;;
    --branch)
      BRANCH="$2"
      shift 2
      ;;
    --dest)
      DEST_DIR="$2"
      shift 2
      ;;
    --)
      shift
      break
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      break
      ;;
  esac
done

if ! command -v git >/dev/null 2>&1; then
  echo "git is required. Install it first: sudo apt-get update && sudo apt-get install -y git"
  exit 1
fi

if [[ -d "${DEST_DIR}/.git" ]]; then
  echo "[1/3] Updating existing repo: ${DEST_DIR}"
  git -C "${DEST_DIR}" fetch origin "${BRANCH}"
  git -C "${DEST_DIR}" checkout "${BRANCH}"
  git -C "${DEST_DIR}" pull --ff-only origin "${BRANCH}"
else
  echo "[1/3] Cloning repo into: ${DEST_DIR}"
  git clone --branch "${BRANCH}" "${REPO_URL}" "${DEST_DIR}"
fi

echo "[2/3] Enter repo"
cd "${DEST_DIR}"

echo "[3/3] Run Orin auto setup/download/test"
bash scripts/orin_auto_setup_download_test.sh "$@"
