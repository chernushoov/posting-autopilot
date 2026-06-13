#!/usr/bin/env bash
# Prod Postgres backup + documented restore (C8 — there was no backup mechanism).
#
# BACKUP (run on the host that runs docker compose, e.g. the Hetzner box):
#   ./scripts/pg_backup.sh
# Writes a compressed custom-format dump to ./backups/ and prints the restore command.
# Keeps the most recent 14 dumps. Schedule it daily, e.g. crontab:
#   15 3 * * *  cd /opt/posting-autopilot && ./scripts/pg_backup.sh >> /var/log/ra_pg_backup.log 2>&1
#
# RESTORE (DANGER — overwrites the live DB; take a fresh backup first):
#   <compose> exec -T postgres pg_restore -U postgres -d ra --clean --if-exists < backups/ra_<ts>.dump
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BACKUP_DIR="${BACKUP_DIR:-$ROOT/backups}"
mkdir -p "$BACKUP_DIR"
TS="$(date +%Y%m%d_%H%M%S)"
OUT="$BACKUP_DIR/ra_${TS}.dump"

# Match the prod overlay when present so we hit the running postgres service.
COMPOSE="docker compose -f docker-compose.yml"
if [ -f docker-compose.prod.yml ]; then
  COMPOSE="$COMPOSE -f docker-compose.prod.yml"
fi

echo "[pg_backup] dumping database 'ra' -> $OUT"
# -Fc = custom format (compressed, supports pg_restore --clean). -T avoids a TTY.
$COMPOSE exec -T postgres pg_dump -U postgres -Fc ra > "$OUT"

if [ ! -s "$OUT" ]; then
  echo "[pg_backup] ERROR: dump is empty — backup FAILED, not pruning." >&2
  rm -f "$OUT"
  exit 1
fi

SIZE="$(du -h "$OUT" | cut -f1)"
echo "[pg_backup] OK: $OUT ($SIZE)"

# Retention: keep the 14 newest dumps.
ls -1t "$BACKUP_DIR"/ra_*.dump 2>/dev/null | tail -n +15 | xargs -r rm -f || true

cat <<EOF

Restore (DANGER — overwrites current DB):
  $COMPOSE exec -T postgres pg_restore -U postgres -d ra --clean --if-exists < "$OUT"

Pull a copy off-box (from your laptop):
  scp -i ~/.ssh/posting_autopilot_hetzner root@167.233.98.210:"$OUT" ./
EOF
