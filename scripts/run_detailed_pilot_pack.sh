#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_URL="${1:-${POSTING_AUTOPILOT_BASE_URL:-https://posting-autopilot-next.vercel.app}}"
RC=0

echo "== Launch gate =="
if ! python3 "${ROOT_DIR}/scripts/final_launch_gate.py" "${BASE_URL}"; then
  RC=1
fi

echo
echo "== Live settings probe =="
if ! bash "${ROOT_DIR}/scripts/live_settings_probe.sh" "${BASE_URL}"; then
  RC=1
fi

echo
echo "== Live settings matrix =="
if ! python3 "${ROOT_DIR}/scripts/live_settings_matrix_probe.py" "${BASE_URL}"; then
  RC=1
fi

echo
echo "== Multilingual pilot =="
if ! python3 "${ROOT_DIR}/scripts/multilingual_pilot_check.py"; then
  RC=1
fi

echo
echo "DETAILED PILOT PACK COMPLETE"
exit "${RC}"
