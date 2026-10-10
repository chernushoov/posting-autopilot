#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
REF="${FLEET_REF:-ccr-6619f392-28owwd}"
BASE="https://raw.githubusercontent.com/chernushoov/posting-autopilot/${REF}/ops/fleet/android"
D="$HOME/.fleet-src"
mkdir -p "$D"
for f in bootstrap.sh lib.sh watchdog.sh daily_report.sh start_bridge.sh agent.env.example CLAUDE.md; do
  curl -fsSL "$BASE/$f" -o "$D/$f"
done
exec bash "$D/bootstrap.sh" "$@"
