#!/usr/bin/env bash
# Bad-input resistance smoke for posting-autopilot-next.
# Verifies the app does NOT 5xx on the kinds of inputs an honest mistake or a
# crawler will produce. Each case must respond 2xx (with inline error) or 3xx
# (sane redirect with flashed error). Anything that returns 5xx is a regression.
set -u

BASE_URL="${1:-${POSTING_AUTOPILOT_BASE_URL:-https://posting-autopilot-next.vercel.app}}"
TMPDIR="$(mktemp -d)"
COOKIES="${TMPDIR}/cookies.txt"
trap 'rm -rf "${TMPDIR}"' EXIT

pass() { printf 'PASS %s\n' "$1"; }
fail() { printf 'FAIL %s — got %s, expected non-5xx\n' "$1" "$2"; FAILED=$((FAILED+1)); }

FAILED=0

curl -s -c "${COOKIES}" -o /dev/null "${BASE_URL}/login"
curl -s -c "${COOKIES}" -b "${COOKIES}" -o /dev/null \
  -X POST "${BASE_URL}/login?next=/" \
  -d "email=demo@postingautopilot.local" \
  -d "password=demo123"

assert_not_5xx() {
  local label="$1"
  local code="$2"
  if [[ "$code" =~ ^5 ]]; then
    fail "$label" "$code"
  else
    pass "$label (got $code)"
  fi
}

post_status() {
  curl -s -b "${COOKIES}" -o /dev/null -w '%{http_code}' \
    -X POST "${BASE_URL}$1" "${@:2}"
}

get_status() {
  curl -s -b "${COOKIES}" -o /dev/null -w '%{http_code}' "${BASE_URL}$1"
}

# ── Schedule POST resistance ────────────────────────────────────────────
assert_not_5xx "schedule: empty ad_id" \
  "$(post_status "/schedule" -d "ad_id=" -d "title=t" -d "start_at=2026-06-01T10:00" -d "cadence=daily" -d "timezone=Asia/Jerusalem")"

assert_not_5xx "schedule: ad_id=abc (non-int)" \
  "$(post_status "/schedule" -d "ad_id=abc" -d "title=t" -d "start_at=2026-06-01T10:00" -d "cadence=daily" -d "timezone=Asia/Jerusalem")"

assert_not_5xx "schedule: ad_id=999999 (not yours)" \
  "$(post_status "/schedule" -d "ad_id=999999" -d "title=t" -d "start_at=2026-06-01T10:00" -d "cadence=daily" -d "timezone=Asia/Jerusalem")"

assert_not_5xx "schedule: start_at=not-a-date" \
  "$(post_status "/schedule" -d "ad_id=1" -d "title=t" -d "start_at=not-a-date" -d "cadence=daily" -d "timezone=Asia/Jerusalem")"

assert_not_5xx "schedule: empty start_at" \
  "$(post_status "/schedule" -d "ad_id=1" -d "title=t" -d "start_at=" -d "cadence=daily" -d "timezone=Asia/Jerusalem")"

assert_not_5xx "schedule: cadence=garbage" \
  "$(post_status "/schedule" -d "ad_id=1" -d "title=t" -d "start_at=2026-06-01T10:00" -d "cadence=garbage" -d "timezone=Asia/Jerusalem")"

# ── /ads/new POST resistance ────────────────────────────────────────────
assert_not_5xx "ads/new: empty title" \
  "$(post_status "/ads/new" -d "title=" -d "primary_text=text" -d "group_ids=1")"

assert_not_5xx "ads/new: group_ids=abc (non-int)" \
  "$(post_status "/ads/new" -d "title=t" -d "primary_text=text" -d "group_ids=abc")"

assert_not_5xx "ads/new: group_ids=99999999999 (overflow-ish int)" \
  "$(post_status "/ads/new" -d "title=t" -d "primary_text=text" -d "group_ids=99999999999")"

assert_not_5xx "ads/new: empty body" \
  "$(post_status "/ads/new" -d "")"

# ── /history GET filter resistance ─────────────────────────────────────
assert_not_5xx "history GET ?status=garbage" \
  "$(get_status "/history?status=garbage")"

assert_not_5xx "history GET ?status=<xss>" \
  "$(get_status "/history?status=%3Cscript%3E")"

# ── /history/<id>/status POST resistance ───────────────────────────────
assert_not_5xx "history POST item_id=0 status=posted" \
  "$(post_status "/history/0/status" -d "status=posted")"

assert_not_5xx "history POST item_id=99999 status=posted" \
  "$(post_status "/history/99999/status" -d "status=posted")"

assert_not_5xx "history POST item_id=1 status=garbage" \
  "$(post_status "/history/1/status" -d "status=garbage")"

# ── /telegram/test-message POST resistance ─────────────────────────────
assert_not_5xx "telegram/test-message: empty chat_ref" \
  "$(post_status "/telegram/test-message" -d "chat_ref=" -d "text=hi")"

assert_not_5xx "telegram/test-message: bot self-handle" \
  "$(post_status "/telegram/test-message" -d "chat_ref=@AutopillotRecruit_bot" -d "text=hi")"

assert_not_5xx "telegram/test-message: seeded sample ref" \
  "$(post_status "/telegram/test-message" -d "chat_ref=@startup_hiring_alerts" -d "text=hi")"

# ── /settings POST resistance ──────────────────────────────────────────
assert_not_5xx "settings POST: empty body" \
  "$(post_status "/settings" -d "")"

# ── /facebook-connect POST resistance ──────────────────────────────────
assert_not_5xx "facebook-connect POST: unknown provider" \
  "$(post_status "/facebook-connect" -d "provider=unknown" -d "account_name=x")"

if [[ "$FAILED" -gt 0 ]]; then
  printf '\nBAD-INPUT SMOKE FAILED %s — %d test(s) returned 5xx\n' "${BASE_URL}" "$FAILED"
  exit 1
fi
printf '\nBAD-INPUT SMOKE OK %s — zero 5xx on hostile input\n' "${BASE_URL}"
