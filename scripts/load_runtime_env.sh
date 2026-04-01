#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_ENV_FILE="${ROOT_DIR}/.env.runtime"

load_env_file() {
  local file_path="$1"
  [[ -f "$file_path" ]] || return 0

  while IFS= read -r raw_line || [[ -n "$raw_line" ]]; do
    local line="${raw_line%$'\r'}"
    [[ -z "$line" ]] && continue
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" != *=* ]] && continue

    local key="${line%%=*}"
    local value="${line#*=}"

    key="$(printf '%s' "$key" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
    value="$(printf '%s' "$value" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

    if [[ "$value" == \"*\" && "$value" == *\" ]]; then
      value="${value:1:${#value}-2}"
    elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
      value="${value:1:${#value}-2}"
    fi

    export "$key=$value"
  done < "$file_path"
}

load_env_file "$RUNTIME_ENV_FILE"

load_keychain_secret() {
  local key_name="$1"
  local service_name="$2"
  if [[ -n "${!key_name:-}" ]]; then
    return 0
  fi
  if ! command -v security >/dev/null 2>&1; then
    return 0
  fi
  local secret
  secret="$(security find-generic-password -w -s "$service_name" 2>/dev/null || true)"
  if [[ -n "$secret" ]]; then
    export "$key_name=$secret"
  fi
}

load_keychain_secret "RECRUITBOT_TELEGRAM_BOT_TOKEN" "recruitbot_telegram_bot_token"
load_keychain_secret "RECRUITBOT_AI_PROVIDER" "recruitbot_ai_provider"
load_keychain_secret "RECRUITBOT_AI_API_KEY" "recruitbot_ai_api_key"

