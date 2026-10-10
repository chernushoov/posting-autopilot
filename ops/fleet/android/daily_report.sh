#!/data/data/com.termux/files/usr/bin/bash
set -u
. "$HOME/fleet/lib.sh"

bat=$(battery_json)
pct=$(echo "$bat" | jq -r '.percentage // "?"')
plug=$(echo "$bat" | jq -r '.plugged // "?"')
temp=$(echo "$bat" | jq -r '.temperature // "?"')
health=$(echo "$bat" | jq -r '.health // "?"')

egress=$(curl -fsS -m 25 -x "$(proxy_url)" https://ipinfo.io/json 2>/dev/null || echo '{}')
eip=$(echo "$egress" | jq -r '.ip // "DOWN"')
org=$(echo "$egress" | jq -r '.org // "?"')
city=$(echo "$egress" | jq -r '.city // "?"')

proxy_sv=$(sv status fleet-proxy 2>/dev/null | cut -d: -f1 || echo "?")
bridge=$(tmux has-session -t claude 2>/dev/null && echo up || echo down)
disk=$(df -h "$HOME" 2>/dev/null | awk 'NR==2{print $4" free"}')
ipchg=$({ wc -l < "$STATE/egress_changes.log"; } 2>/dev/null || echo 0)
inc=$(tail -n 10 "$STATE/incidents.log" 2>/dev/null || true)

msg="DAILY $(date '+%Y-%m-%d')
battery: ${pct}% ${plug} ${temp}C ${health}
proxy: ${proxy_sv} | egress ${eip} | ${org} | ${city}
egress IP changes (24h): ${ipchg}
claude bridge: ${bridge}
disk: ${disk}
incidents (24h):
${inc:-none}"

notify "$msg"

[ -f "$STATE/incidents.log" ] && mv "$STATE/incidents.log" "$STATE/incidents.log.1"
[ -f "$STATE/egress_changes.log" ] && mv "$STATE/egress_changes.log" "$STATE/egress_changes.log.1"
exit 0
