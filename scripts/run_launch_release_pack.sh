#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_URL="${1:-${POSTING_AUTOPILOT_BASE_URL:-https://posting-autopilot-next.vercel.app}}"
RC=0

echo "== Launch gate snapshot =="
if ! python3 "${ROOT_DIR}/scripts/write_launch_gate_snapshot.py" "${BASE_URL}"; then
  RC=1
fi

echo
echo "== Live settings probe =="
if ! bash "${ROOT_DIR}/scripts/live_settings_probe.sh" "${BASE_URL}"; then
  RC=1
fi

echo
echo "RELEASE PACK COMPLETE"
exit "${RC}"
