#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
FLEET="$HOME/fleet"
SVC="$PREFIX/var/service"
WITH_CLAUDE=1
[ "${1:-}" = "--no-claude" ] && WITH_CLAUDE=0

echo "== packages"
pkg update -y
pkg upgrade -y
pkg install -y termux-api termux-services cronie tinyproxy curl jq tmux openssh proot-distro coreutils findutils nano

echo "== fleet dir"
mkdir -p "$FLEET/state" "$HOME/.termux/boot" "$HOME/agent"
for f in lib.sh watchdog.sh daily_report.sh start_bridge.sh; do
  install -m 0755 "$SRC/$f" "$FLEET/$f"
done
install -m 0644 "$SRC/CLAUDE.md" "$HOME/agent/CLAUDE.md"

if [ ! -f "$FLEET/agent.env" ]; then
  install -m 0600 "$SRC/agent.env.example" "$FLEET/agent.env"
  pass=$(head -c 64 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 28)
  sed -i "s/^PROXY_PASS=.*/PROXY_PASS=${pass}/" "$FLEET/agent.env"
fi
chmod 600 "$FLEET/agent.env"
set -a; . "$FLEET/agent.env"; set +a

echo "== proxy"
mkdir -p "$PREFIX/var/log" "$PREFIX/var/run"
cat > "$FLEET/tinyproxy.conf" <<EOF
Port ${PROXY_PORT}
Listen 0.0.0.0
Timeout 600
MaxClients 64
Allow 127.0.0.1
Allow 100.64.0.0/10
BasicAuth ${PROXY_USER} ${PROXY_PASS}
DisableViaHeader Yes
LogLevel Warning
LogFile "${PREFIX}/var/log/fleet-proxy.log"
PidFile "${PREFIX}/var/run/fleet-proxy.pid"
EOF
chmod 600 "$FLEET/tinyproxy.conf"
mkdir -p "$SVC/fleet-proxy"
cat > "$SVC/fleet-proxy/run" <<EOF
#!${PREFIX}/bin/sh
exec tinyproxy -d -c ${FLEET}/tinyproxy.conf 2>&1
EOF
chmod 0755 "$SVC/fleet-proxy/run"

echo "== cron"
crontab_tmp="$(mktemp)"
{ crontab -l 2>/dev/null | grep -v '/fleet/' | grep -v '^PATH=\|^SVDIR=\|^HOME=' || true
  echo "HOME=$HOME"
  echo "PATH=$PREFIX/bin"
  echo "SVDIR=$SVC"
  echo "*/5 * * * * $FLEET/watchdog.sh >/dev/null 2>&1"
  echo "50 8 * * * $FLEET/daily_report.sh >/dev/null 2>&1"
} > "$crontab_tmp"
crontab "$crontab_tmp"
rm -f "$crontab_tmp"

echo "== boot"
cat > "$HOME/.termux/boot/00-fleet" <<EOF
#!${PREFIX}/bin/sh
termux-wake-lock
. ${PREFIX}/etc/profile.d/start-services.sh
sleep 20
${FLEET}/start_bridge.sh
EOF
chmod 0755 "$HOME/.termux/boot/00-fleet"

echo "== services"
export SVDIR="$SVC"
set +u
. "$PREFIX/etc/profile.d/start-services.sh" || true
set -u
sleep 3
sv-enable crond || true
sv-enable sshd || true
sv-enable fleet-proxy || true
termux-wake-lock || true

if [ "$WITH_CLAUDE" = 1 ]; then
  echo "== claude (ubuntu proot)"
  proot-distro install ubuntu || true
  proot-distro login ubuntu --termux-home -- bash -lc '
    export DEBIAN_FRONTEND=noninteractive PATH=/root/.local/bin:$PATH
    apt-get update && apt-get install -y curl ca-certificates git ripgrep
    curl -fsSL https://claude.ai/install.sh | bash || true
    command -v claude || { apt-get install -y nodejs npm && npm install -g @anthropic-ai/claude-code; }
    claude --version' \
    || echo "WARN: claude install failed; rerun: bash $SRC/bootstrap.sh"
fi

echo "== self-test"
sleep 3
egress=$(curl -fsS -m 25 -x "http://${PROXY_USER}:${PROXY_PASS}@127.0.0.1:${PROXY_PORT}" https://ipinfo.io/json || echo '{}')
echo "proxy egress: $(echo "$egress" | jq -c '{ip,org,city}')"
"$FLEET/watchdog.sh" || true

cat <<EOF

DONE.
Proxy for prod (.env.prod):
  FB_PROXY_SERVER=http://<tailscale IP of this phone>:${PROXY_PORT}
  FB_PROXY_USERNAME=${PROXY_USER}
  FB_PROXY_PASSWORD=${PROXY_PASS}
Next: fill TG_BOT_TOKEN / TG_CHAT_ID in $FLEET/agent.env
Then: proot-distro login ubuntu --termux-home  ->  cd ~/agent && claude  (login + trust, then /exit)
Then: $FLEET/start_bridge.sh --enable
EOF
