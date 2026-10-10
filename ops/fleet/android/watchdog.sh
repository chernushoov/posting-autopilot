#!/data/data/com.termux/files/usr/bin/bash
set -u
. "$HOME/fleet/lib.sh"

LOCK="$STATE/watchdog.lock"
mkdir "$LOCK" 2>/dev/null || { [ -n "$(find "$LOCK" -mmin +10 2>/dev/null)" ] && rm -rf "$LOCK" && mkdir "$LOCK"; } || exit 0
trap 'rm -rf "$LOCK"' EXIT

THRESHOLD="${FAIL_THRESHOLD:-2}"

if [ -f "$STATE/cmd" ]; then
  mv "$STATE/cmd" "$STATE/cmd.run"
  while read -r c; do
    case "$c" in
      restart-proxy) sv restart fleet-proxy >/dev/null 2>&1; log_incident "cmd restart-proxy" ;;
      report-now) "$FLEET/daily_report.sh" ;;
      *) log_incident "cmd rejected: $c" ;;
    esac
  done < "$STATE/cmd.run"
  rm -f "$STATE/cmd.run"
fi

track() {
  local name="$1" status="$2" detail="${3:-}"
  local f="$STATE/$name.fails" n
  n=$(cat "$f" 2>/dev/null || echo 0)
  if [ "$status" = ok ]; then
    if [ "$n" -ge "$THRESHOLD" ]; then
      log_incident "RECOVERED $name"
      notify "RECOVERED: $name"
    fi
    echo 0 > "$f"
  else
    n=$((n + 1))
    echo "$n" > "$f"
    if [ "$n" -eq "$THRESHOLD" ]; then
      log_incident "DOWN $name $detail"
      notify "DOWN: $name $detail"
    fi
  fi
}

if ! curl -fsS -m 10 -o /dev/null https://www.google.com/generate_204; then
  echo "$(ts) phone offline, checks skipped" >> "$STATE/offline.log"
  exit 0
fi

for pair in ${CHECK_URLS:-}; do
  name="${pair%%=*}"
  url="${pair#*=}"
  code=$(curl -sS -m 20 -o /dev/null -w '%{http_code}' "$url" 2>/dev/null || echo 000)
  if [ "$code" = 200 ]; then track "$name" ok; else track "$name" fail "HTTP $code $url"; fi
done

ip=$(curl -fsS -m 25 -x "$(proxy_url)" https://api.ipify.org 2>/dev/null || true)
if [ -n "$ip" ]; then
  prev=$(cat "$STATE/egress_ip" 2>/dev/null || true)
  echo "$ip" > "$STATE/egress_ip"
  [ -n "$prev" ] && [ "$prev" != "$ip" ] && echo "$(ts) $prev -> $ip" >> "$STATE/egress_changes.log"
  track proxy ok
else
  track proxy fail "local proxy :${PROXY_PORT} not serving"
  sv up fleet-proxy >/dev/null 2>&1 || true
fi

bat=$(battery_json)
pct=$(echo "$bat" | jq -r '.percentage // empty')
plug=$(echo "$bat" | jq -r '.plugged // empty')
temp=$(echo "$bat" | jq -r '.temperature // empty' | cut -d. -f1)
if [ -n "$pct" ]; then
  if [ "$pct" -lt "${BATTERY_MIN:-30}" ] && [ "$plug" = UNPLUGGED ]; then
    track power fail "battery ${pct}% unplugged"
  else
    track power ok
  fi
fi
if [ -n "$temp" ]; then
  if [ "$temp" -gt "${TEMP_MAX:-45}" ]; then track heat fail "battery ${temp}C"; else track heat ok; fi
fi

if [ -f "$FLEET/claude.ok" ] && ! tmux has-session -t claude 2>/dev/null; then
  "$FLEET/start_bridge.sh"
  log_incident "bridge restarted"
fi

exit 0
