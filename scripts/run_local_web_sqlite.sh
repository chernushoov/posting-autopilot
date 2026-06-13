#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PY="${ROOT_DIR}/.venv-local/bin/python"
VENV_FLASK="${ROOT_DIR}/.venv-local/bin/flask"

if [[ ! -x "${VENV_FLASK}" || ! -x "${VENV_PY}" ]]; then
  echo "Missing .venv-local Flask runtime. Expected: ${ROOT_DIR}/.venv-local" >&2
  exit 1
fi

cd "${ROOT_DIR}"

set -a
[[ -f .env ]] && source .env
[[ -f .env.runtime ]] && source .env.runtime
export DATABASE_URL="${LOCAL_DATABASE_URL:-sqlite:///ra.db}"
export FLASK_APP="app.factory:create_app"
export FLASK_DEBUG="${FLASK_DEBUG:-0}"
set +a

"${VENV_PY}" -c "from app.factory import create_app; create_app()"

exec "${VENV_FLASK}" run \
  --host "${HOST:-127.0.0.1}" \
  --port "${PORT:-8080}"
