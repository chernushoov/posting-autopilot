#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
exec ./deploy-hetzner.sh --skip-install "$@"
