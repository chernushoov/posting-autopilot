#!/usr/bin/env bash
# Daily backup for posting-autopilot.
#   1) Postgres logical dump (gzip)
#   2) Browser/Telegram session files from the ra_data volume (NOT in pg_dump!)
# Local copies under ./backups with 7-day rotation. Off-box upload is one env away
# (set BACKUP_RCLONE_REMOTE to e.g. "b2:pa-backups" once object storage is added).
#
# Restore (DB):   gunzip -c backups/db-<TS>.sql.gz | docker compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"'
# Restore (sess): docker compose exec -T web tar -xzf - -C /app/data < backups/sessions-<TS>.tar.gz
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE="docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml"
TS="$(date +%Y%m%d-%H%M%S)"
BK="$(pwd)/backups"
KEEP=7
mkdir -p "$BK"

# 1) Postgres — use the container's own POSTGRES_USER/DB env (no hardcoded creds)
$COMPOSE exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' | gzip > "$BK/db-$TS.sql.gz"

# 2) Session files (the irreplaceable FB/TG logins) from the shared volume
$COMPOSE exec -T web sh -c 'cd /app/data && tar -czf - fb_sessions tg_sessions 2>/dev/null' > "$BK/sessions-$TS.tar.gz" || true

# 3) Rotate — keep newest $KEEP of each
ls -1t "$BK"/db-*.sql.gz 2>/dev/null      | tail -n +$((KEEP+1)) | xargs -r rm -f
ls -1t "$BK"/sessions-*.tar.gz 2>/dev/null | tail -n +$((KEEP+1)) | xargs -r rm -f

# 4) Off-box (optional, activates when BACKUP_RCLONE_REMOTE is set)
if [ -n "${BACKUP_RCLONE_REMOTE:-}" ] && command -v rclone >/dev/null 2>&1; then
  rclone copy "$BK/db-$TS.sql.gz"       "$BACKUP_RCLONE_REMOTE/" --quiet || echo "WARN: off-box db upload failed"
  rclone copy "$BK/sessions-$TS.tar.gz" "$BACKUP_RCLONE_REMOTE/" --quiet || echo "WARN: off-box sessions upload failed"
fi

DBSZ=$(du -h "$BK/db-$TS.sql.gz" | cut -f1)
echo "[backup] $TS ok — db=$DBSZ sessions=$(du -h "$BK/sessions-$TS.tar.gz" 2>/dev/null | cut -f1 || echo 0) off_box=${BACKUP_RCLONE_REMOTE:-none}"
