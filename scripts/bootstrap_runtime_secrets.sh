#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_ENV_FILE="${ROOT_DIR}/.env.runtime"

TOKEN="${RECRUITBOT_TELEGRAM_BOT_TOKEN:-}"
AI_PROVIDER_VALUE="${RECRUITBOT_AI_PROVIDER:-}"
AI_KEY_VALUE="${RECRUITBOT_AI_API_KEY:-}"
WRITE_FILE=0

usage() {
  cat <<'EOF'
Usage:
  bash scripts/bootstrap_runtime_secrets.sh [--token TOKEN] [--ai-provider PROVIDER] [--ai-key KEY] [--write-file]

Behavior:
  - stores provided values in macOS Keychain under recruitbot_* service names
  - optionally writes a local .env.runtime file when --write-file is passed
  - does not print raw secrets
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --token)
      TOKEN="${2:-}"
      shift 2
      ;;
    --ai-provider)
      AI_PROVIDER_VALUE="${2:-}"
      shift 2
      ;;
    --ai-key)
      AI_KEY_VALUE="${2:-}"
      shift 2
      ;;
    --write-file)
      WRITE_FILE=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

store_keychain() {
  local service_name="$1"
  local value="$2"
  [[ -n "$value" ]] || return 0
  security add-generic-password -U -a "${USER}" -s "$service_name" -w "$value" >/dev/null
}

store_keychain "recruitbot_telegram_bot_token" "$TOKEN"
store_keychain "recruitbot_ai_provider" "$AI_PROVIDER_VALUE"
store_keychain "recruitbot_ai_api_key" "$AI_KEY_VALUE"

if [[ "$WRITE_FILE" -eq 1 ]]; then
  {
    echo "# Local runtime-only overrides"
    [[ -n "$TOKEN" ]] && echo "RECRUITBOT_TELEGRAM_BOT_TOKEN=${TOKEN}"
    [[ -n "$AI_PROVIDER_VALUE" ]] && echo "RECRUITBOT_AI_PROVIDER=${AI_PROVIDER_VALUE}"
    [[ -n "$AI_KEY_VALUE" ]] && echo "RECRUITBOT_AI_API_KEY=${AI_KEY_VALUE}"
  } > "$RUNTIME_ENV_FILE"
fi

echo "stored runtime secrets:"
[[ -n "$TOKEN" ]] && echo "- recruitbot_telegram_bot_token"
[[ -n "$AI_PROVIDER_VALUE" ]] && echo "- recruitbot_ai_provider"
[[ -n "$AI_KEY_VALUE" ]] && echo "- recruitbot_ai_api_key"
[[ "$WRITE_FILE" -eq 1 ]] && echo "- wrote ${RUNTIME_ENV_FILE}"
echo "next:"
echo "bash scripts/runtime_env_status.py --json 2>/dev/null || python3 scripts/runtime_env_status.py --json"
echo "bash scripts/runtime_check_with_env.sh --json"
