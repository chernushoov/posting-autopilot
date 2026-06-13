#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPS_DIR="${ROOT_DIR}/ops/live_vacancy_4_hires"
GENERATED_DIR="${OPS_DIR}/generated"
READINESS_GATE="${ROOT_DIR}/scripts/launch_readiness_gate.py"

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
READINESS_EXIT=0
python3 "${READINESS_GATE}" || READINESS_EXIT=$?
if [[ "${READINESS_EXIT}" -eq 2 ]]; then
  echo
  echo "Launch prep completed with blockers."
else
  echo "Done."
fi
echo "Next:"
echo "- fill missing intake fields"
echo "- rerun: bash scripts/sunday_launch_prep.sh"
echo "- if readiness is clean enough, post first-wave manual sources"
exit "${READINESS_EXIT}"
