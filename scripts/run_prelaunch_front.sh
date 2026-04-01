#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_URL="${POSTING_AUTOPILOT_BASE_URL:-https://posting-autopilot-next.vercel.app}"

echo "== Runtime health =="
bash "${ROOT_DIR}/scripts/runtime_check_with_env.sh" --json

echo
echo "== Local guardrails =="
bash "${ROOT_DIR}/scripts/compose_with_runtime.sh" exec -T web python scripts/launch_guardrail_check.py

echo
echo "== Live deploy smoke =="
bash "${ROOT_DIR}/scripts/live_deploy_smoke.sh" "${BASE_URL}"

echo
echo "PRELAUNCH FRONT OK"
