#!/usr/bin/env bash
set -euo pipefail
# Production launcher — build + (re)start the full stack with the prod overlay.
# Usage: ./deploy.sh
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  echo "ERROR: .env missing. Run: cp .env.production.example .env && nano .env"
  exit 1
fi
touch .env.runtime  # compose env_file expects it to exist (may be empty)

echo "[deploy] building + starting stack (prod overlay)..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo "[deploy] services:"
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

cat <<'EOF'

[deploy] done.
First deploy only — initialize the DB:
  docker compose exec web python -m scripts.seed
Verify:
  curl -s https://<your-domain>/health
EOF
