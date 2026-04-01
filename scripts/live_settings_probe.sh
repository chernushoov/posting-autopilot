#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-${POSTING_AUTOPILOT_BASE_URL:-https://posting-autopilot-next.vercel.app}}"
OUT_DIR="${2:-${POSTING_AUTOPILOT_PROBE_DIR:-ops/prelaunch_artifacts/live_settings_probe}}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${ROOT_DIR}/${OUT_DIR}"
mkdir -p "${TARGET_DIR}"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${TARGET_DIR}/${STAMP}"
mkdir -p "${RUN_DIR}"

COOKIE_JAR="${RUN_DIR}/cookies.txt"
LOGIN_HEADERS="${RUN_DIR}/login.headers"
SETTINGS_HEADERS="${RUN_DIR}/settings_post.headers"
SETTINGS_BODY="${RUN_DIR}/settings_post.body.html"
SUMMARY_JSON="${RUN_DIR}/summary.json"

SETTINGS_NAME="QA Probe ${STAMP}"
SETTINGS_CTA="Reply ${STAMP}"
SETTINGS_WINDOW="11:00-17:00"

curl -s -D "${LOGIN_HEADERS}" -o /dev/null -c "${COOKIE_JAR}" -b "${COOKIE_JAR}" \
  -X POST "${BASE_URL}/login?next=/settings" \
  -d "email=demo@postingautopilot.local" \
  -d "password=demo123"

STATUS="$(
  curl -s -D "${SETTINGS_HEADERS}" -o "${SETTINGS_BODY}" -b "${COOKIE_JAR}" \
    -X POST "${BASE_URL}/settings" \
    -d "full_name=${SETTINGS_NAME// /+}" \
    -d "timezone=Asia/Jerusalem" \
    -d "default_cta=${SETTINGS_CTA// /+}" \
    -d "posting_window=${SETTINGS_WINDOW}" \
    -d "notifications_enabled=on" \
    -w '%{http_code}'
)"

python3 - <<'PY' "${SUMMARY_JSON}" "${BASE_URL}" "${STATUS}" "${SETTINGS_HEADERS}" "${SETTINGS_BODY}" "${RUN_DIR}"
import json
import sys
from pathlib import Path

summary_path = Path(sys.argv[1])
base_url = sys.argv[2]
status = sys.argv[3]
headers_path = Path(sys.argv[4])
body_path = Path(sys.argv[5])
run_dir = Path(sys.argv[6])

payload = {
    "base_url": base_url,
    "status_code": int(status),
    "ok": status in {"200", "302"},
    "headers_path": str(headers_path),
    "body_path": str(body_path),
    "run_dir": str(run_dir),
}
summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2, ensure_ascii=False))
PY

echo "Probe artifacts: ${RUN_DIR}"

if [[ "${STATUS}" != "200" && "${STATUS}" != "302" ]]; then
  exit 1
fi
