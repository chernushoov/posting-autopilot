#!/data/data/com.termux/files/usr/bin/bash
export PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
export HOME="${HOME:-/data/data/com.termux/files/home}"
export PATH="$PREFIX/bin:$PATH"
export SVDIR="$PREFIX/var/service"
FLEET="$HOME/fleet"
STATE="$FLEET/state"
mkdir -p "$STATE"
set -a
. "$FLEET/agent.env"
set +a

ts() { date '+%Y-%m-%d %H:%M:%S'; }

log_incident() { echo "$(ts) $1" >> "$STATE/incidents.log"; }

tg_send() {
  [ -n "${TG_BOT_TOKEN:-}" ] && [ -n "${TG_CHAT_ID:-}" ] || return 0
  curl -fsS -m 20 -o /dev/null -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TG_CHAT_ID}" --data-urlencode "text=$1" || true
}

notify() {
  timeout 10 termux-notification --id fleet --title "android-agent" --content "$1" >/dev/null 2>&1 || true
  tg_send "[android-agent] $1"
}

proxy_url() { echo "http://${PROXY_USER}:${PROXY_PASS}@127.0.0.1:${PROXY_PORT}"; }

battery_json() { timeout 15 termux-battery-status 2>/dev/null || echo '{}'; }
