#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPS_DIR="${ROOT_DIR}/ops/live_vacancy_4_hires"
GENERATED_DIR="${OPS_DIR}/generated"

mkdir -p "${GENERATED_DIR}"

echo "[1/3] Building live vacancy pack"
python3 "${ROOT_DIR}/scripts/build_live_vacancy_pack.py"

echo
echo "[2/3] Checking Sunday readiness"
python3 "${ROOT_DIR}/scripts/sunday_readiness_check.py"

echo
echo "[3/3] Capturing runtime status"
python3 "${ROOT_DIR}/scripts/runtime_env_status.py" --json > "${GENERATED_DIR}/runtime_status.json" || true

echo
echo "Done."
echo "Next:"
echo "- fill missing intake fields"
echo "- rerun: bash scripts/sunday_launch_prep.sh"
echo "- if readiness is clean enough, post first-wave manual sources"
