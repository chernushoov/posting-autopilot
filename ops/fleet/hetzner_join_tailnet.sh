#!/usr/bin/env bash
# Usage (on prod, /opt/posting-autopilot):
#   ops/fleet/hetzner_join_tailnet.sh <TS_AUTHKEY tagged tag:prod> <PHONE_TS_IP> <PROXY_USER> <PROXY_PASS> [--apply]
# Without --apply: joins tailnet + tests the phone proxy from host and from the worker container. No env/container changes.
set -euo pipefail

AUTHKEY="${1:?authkey}"
PHONE_IP="${2:?phone tailscale ip}"
PUSER="${3:?proxy user}"
PPASS="${4:?proxy pass}"
APPLY="${5:-}"
ROOT=/opt/posting-autopilot
PORT=8888
PROXY="http://${PUSER}:${PPASS}@${PHONE_IP}:${PORT}"
DC=(docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml)
export APP_ENV_FILE=.env.prod

cd "$ROOT"

if ! command -v tailscale >/dev/null; then
  curl -fsSL https://tailscale.com/install.sh | sh
fi
if ! tailscale status >/dev/null 2>&1; then
  tailscale up --authkey "$AUTHKEY" --hostname pa-prod --advertise-tags=tag:prod --accept-dns=false
fi
tailscale ip -4

echo "== host -> phone proxy"
host_json=$(curl -fsS -m 30 -x "$PROXY" https://ipinfo.io/json)
echo "$host_json"
direct_ip=$(curl -fsS -m 15 https://api.ipify.org)
proxy_ip=$(echo "$host_json" | python3 -c 'import json,sys;print(json.load(sys.stdin)["ip"])')
[ "$proxy_ip" != "$direct_ip" ] || { echo "FAIL: proxy egress == datacenter IP"; exit 1; }

echo "== worker container -> phone proxy"
"${DC[@]}" exec -T worker python - "$PROXY" <<'PY'
import sys, urllib.request
h = urllib.request.ProxyHandler({"http": sys.argv[1], "https": sys.argv[1]})
print(urllib.request.build_opener(h).open("https://ipinfo.io/json", timeout=30).read().decode())
PY

if [ "$APPLY" != "--apply" ]; then
  echo "OK. Dry run only. Re-run with --apply to write FB_PROXY_* and recreate web+worker."
  exit 0
fi

ts=$(date +%Y%m%d%H%M%S)
for f in .env.prod .env; do
  [ -f "$f" ] || continue
  cp -p "$f" "$f.bak.$ts"
  sed -i '/^FB_PROXY_SERVER=/d;/^FB_PROXY_USERNAME=/d;/^FB_PROXY_PASSWORD=/d' "$f"
  printf 'FB_PROXY_SERVER=http://%s:%s\nFB_PROXY_USERNAME=%s\nFB_PROXY_PASSWORD=%s\n' "$PHONE_IP" "$PORT" "$PUSER" "$PPASS" >> "$f"
done

"${DC[@]}" up -d --force-recreate web worker

sleep 20
"${DC[@]}" exec -T worker python -c \
  'from common.fb_browser_poster import fb_proxy_config as c; x=c() or {}; print("FB proxy:", x.get("server"))'
"${DC[@]}" exec -T web python -c \
  'import urllib.request;print("health",urllib.request.urlopen("http://localhost:8000/health",timeout=10).status)'
echo "APPLIED. Backups: .env.prod.bak.$ts .env.bak.$ts"
