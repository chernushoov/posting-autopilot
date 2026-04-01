#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${ROOT_DIR}/scripts/load_runtime_env.sh"

cd "$ROOT_DIR"
exec docker compose "$@"

