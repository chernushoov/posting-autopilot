#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-${POSTING_AUTOPILOT_BASE_URL:-https://posting-autopilot-next.vercel.app}}"
TMPDIR="$(mktemp -d)"
COOKIE_JAR="${TMPDIR}/cookies.txt"
STAMP="$(date +%s)"
AD_TITLE="QA Launch Ad ${STAMP}"
SETTINGS_NAME="QA Smoke ${STAMP}"
SETTINGS_CTA="Reply ${STAMP}"
SETTINGS_WINDOW="11:00-17:00"

pass() { printf 'PASS %s\n' "$1"; }
fail() { printf 'FAIL %s\n' "$1"; exit 1; }
warn() { printf 'WARN %s\n' "$1"; WARNINGS=1; }

fetch_status() {
  curl -s -o /dev/null -w '%{http_code}' "$1"
}

body_contains() {
  local file="$1"
  local needle="$2"
  grep -Fq "$needle" "$file"
}

WARNINGS=0

LOGIN_GET_BODY="${TMPDIR}/login_get.html"
LOGIN_GET_HEADERS="${TMPDIR}/login_get.headers"
LOGIN_GET_STATUS="$(
  curl -s -D "${LOGIN_GET_HEADERS}" -o "${LOGIN_GET_BODY}" -w '%{http_code}' \
    "${BASE_URL}/login?next=/settings"
)"
if [[ "${LOGIN_GET_STATUS}" != "200" ]]; then
  VERCEL_ERROR="$(grep -i '^x-vercel-error:' "${LOGIN_GET_HEADERS}" | tr -d '\r' | awk -F': ' '{print $2}' | tail -n 1 || true)"
  BODY_SUMMARY="$(tr '\n' ' ' < "${LOGIN_GET_BODY}" | sed 's/[[:space:]]\+/ /g' | cut -c1-140)"
  if [[ -n "${VERCEL_ERROR}" ]]; then
    fail "login page unavailable: status ${LOGIN_GET_STATUS}, x-vercel-error ${VERCEL_ERROR}, body ${BODY_SUMMARY}"
  fi
  fail "login page unavailable: status ${LOGIN_GET_STATUS}, body ${BODY_SUMMARY}"
fi
body_contains "${LOGIN_GET_BODY}" "Seeded demo account" || fail "login page missing demo account copy"
pass "login page available"

LOGIN_HEADERS="${TMPDIR}/login_post.headers"
curl -s -D "${LOGIN_HEADERS}" -o /dev/null -c "${COOKIE_JAR}" -b "${COOKIE_JAR}" \
  -X POST "${BASE_URL}/login?next=/settings" \
  -d "email=demo@postingautopilot.local" \
  -d "password=demo123"
grep -iEq "^location: /facebook-connect" "${LOGIN_HEADERS}" || fail "login did not redirect to /facebook-connect"
pass "demo login works"

CONNECT_BODY="${TMPDIR}/facebook_connect.html"
curl -s -b "${COOKIE_JAR}" "${BASE_URL}/facebook-connect" -o "${CONNECT_BODY}"
body_contains "${CONNECT_BODY}" "Step 1 of 5" || fail "facebook connect step missing after login"
body_contains "${CONNECT_BODY}" "https://t.me/AutopillotRecruit_bot" || fail "telegram bot link missing from connect workspace"
body_contains "${CONNECT_BODY}" "@AutopillotRecruit_bot" || fail "real telegram bot handle missing from connect workspace"
if grep -Fq "@startup_hiring_alerts" "${CONNECT_BODY}"; then
  fail "stale seeded telegram chat ref still appears in connect workspace"
fi
pass "facebook connect page reachable"

SETTINGS_POST_HEADERS="${TMPDIR}/settings_post.headers"
SETTINGS_POST_BODY="${TMPDIR}/settings_post.body"
SETTINGS_POST_STATUS="$(
  curl -s -D "${SETTINGS_POST_HEADERS}" -o "${SETTINGS_POST_BODY}" -w '%{http_code}' -b "${COOKIE_JAR}" \
    -X POST "${BASE_URL}/settings" \
    -d "full_name=${SETTINGS_NAME// /+}" \
    -d "timezone=Asia/Jerusalem" \
    -d "default_cta=${SETTINGS_CTA// /+}" \
    -d "posting_window=${SETTINGS_WINDOW}" \
    -d "notifications_enabled=on"
)"
SETTINGS_BODY="${TMPDIR}/settings.html"
curl -s -b "${COOKIE_JAR}" "${BASE_URL}/settings" -o "${SETTINGS_BODY}"
body_contains "${SETTINGS_BODY}" "${SETTINGS_NAME}" || fail "settings value did not persist"
body_contains "${SETTINGS_BODY}" "${SETTINGS_WINDOW}" || fail "settings posting window did not persist"
if [[ "${SETTINGS_POST_STATUS}" == "200" || "${SETTINGS_POST_STATUS}" == "302" ]]; then
  pass "settings save works"
elif [[ "${SETTINGS_POST_STATUS}" == "500" ]]; then
  warn "settings save persisted despite 500 response"
else
  fail "settings save failed with status ${SETTINGS_POST_STATUS}"
fi

AD_HEADERS="${TMPDIR}/ad_post.headers"
curl -s -D "${AD_HEADERS}" -o /dev/null -b "${COOKIE_JAR}" \
  -X POST "${BASE_URL}/ads/new" \
  -d "title=${AD_TITLE// /+}" \
  -d "primary_text=Need+candidate+flow" \
  -d "cta_text=Reply+here" \
  -d "audience=Recruiters" \
  -d "group_ids=1" \
  -d "group_ids=2"
AD_LOCATION="$(grep -i '^location:' "${AD_HEADERS}" | tr -d '\r' | awk '{print $2}')"
[[ "${AD_LOCATION}" == /schedule* ]] || fail "ad creation did not redirect to schedule"
AD_ID="$(printf '%s' "${AD_LOCATION}" | sed -n 's/.*ad_id=\([0-9][0-9]*\).*/\1/p')"
[[ -n "${AD_ID}" ]] || fail "could not parse ad_id from schedule redirect"
pass "ad creation works"

SCHEDULE_HEADERS="${TMPDIR}/schedule_post.headers"
curl -s -D "${SCHEDULE_HEADERS}" -o /dev/null -b "${COOKIE_JAR}" \
  -X POST "${BASE_URL}/schedule" \
  -d "ad_id=${AD_ID}" \
  -d "title=QA+Morning+Run" \
  -d "start_at=2026-03-31T09:00" \
  -d "cadence=daily" \
  -d "timezone=Asia/Jerusalem" \
  -d "notes=qa"
grep -iEq "^location: /history" "${SCHEDULE_HEADERS}" || fail "schedule creation did not redirect to history"
pass "schedule creation works"

HISTORY_BODY="${TMPDIR}/history.html"
curl -s -b "${COOKIE_JAR}" "${BASE_URL}/history" -o "${HISTORY_BODY}"
body_contains "${HISTORY_BODY}" "${AD_TITLE}" || fail "history does not show created ad"
STATUS_PATH="$(grep -oE '/history/[0-9]+/status' "${HISTORY_BODY}" | head -n 1 || true)"
[[ -n "${STATUS_PATH}" ]] || fail "history status action not found"
pass "history displays created run"

curl -s -o /dev/null -b "${COOKIE_JAR}" \
  -X POST "${BASE_URL}${STATUS_PATH}" \
  -d "status=posted" \
  -d "operator_note=qa-check"

UPDATED_HISTORY="${TMPDIR}/history_updated.html"
curl -s -b "${COOKIE_JAR}" "${BASE_URL}/history" -o "${UPDATED_HISTORY}"
body_contains "${UPDATED_HISTORY}" "posted" || fail "history status update did not persist"
pass "history status update works"

if [[ "${WARNINGS}" -ne 0 ]]; then
  printf 'SMOKE DEGRADED %s\n' "${BASE_URL}"
  exit 2
fi

printf 'SMOKE OK %s\n' "${BASE_URL}"
