#!/usr/bin/env bash
set -euo pipefail

SCRIPT_NAME="$(basename "$0")"
DEFAULT_REPO_DIR="/opt/posting-autopilot"
DEFAULT_BRANCH="main"
ENV_FILE=".env.prod"
RUNTIME_ENV_FILE=".env.runtime"
REPO_URL=""
REPO_DIR=""
BRANCH="${DEFAULT_BRANCH}"
RUN_SMOKE=0
SKIP_INSTALL=0

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

fail() {
  log "ERROR: $*"
  exit 1
}

usage() {
  cat <<EOF
Usage: ${SCRIPT_NAME} [options]

Options:
  --repo-url <url>         Git repo URL to clone/pull when not already inside the repo
  --repo-dir <path>        Target directory for clone/pull (default: ${DEFAULT_REPO_DIR})
  --branch <name>          Git branch to deploy (default: ${DEFAULT_BRANCH})
  --env-file <path>        Production env file (default: .env.prod inside repo)
  --runtime-env-file <p>   Optional runtime overlay (default: .env.runtime inside repo)
  --smoke                  Run post-boot smoke checks against /health, /login, /register
  --skip-install           Skip Docker/package installation steps
  -h, --help               Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-url)
      REPO_URL="${2:-}"
      shift 2
      ;;
    --repo-dir)
      REPO_DIR="${2:-}"
      shift 2
      ;;
    --branch)
      BRANCH="${2:-}"
      shift 2
      ;;
    --env-file)
      ENV_FILE="${2:-}"
      shift 2
      ;;
    --runtime-env-file)
      RUNTIME_ENV_FILE="${2:-}"
      shift 2
      ;;
    --smoke)
      RUN_SMOKE=1
      shift
      ;;
    --skip-install)
      SKIP_INSTALL=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "Unknown argument: $1"
      ;;
  esac
done

SUDO=""
if [[ "${EUID}" -ne 0 ]]; then
  SUDO="sudo"
fi

ensure_base_packages() {
  log "Ensuring base packages are available"
  ${SUDO} apt-get update -y
  ${SUDO} apt-get install -y ca-certificates curl git
}

ensure_docker() {
  if command -v docker >/dev/null 2>&1 && ${SUDO} docker compose version >/dev/null 2>&1; then
    log "Docker + compose plugin already present"
    return
  fi
  log "Installing Docker Engine + compose plugin"
  curl -fsSL https://get.docker.com | ${SUDO} sh
  if ! ${SUDO} docker compose version >/dev/null 2>&1; then
    ${SUDO} apt-get install -y docker-compose-plugin
  fi
  ${SUDO} systemctl enable --now docker
}

resolve_repo() {
  if [[ -f "docker-compose.yml" && -f "docker-compose.prod.yml" ]]; then
    REPO_DIR="$(pwd)"
    log "Using current repo directory: ${REPO_DIR}"
    return
  fi

  REPO_DIR="${REPO_DIR:-${DEFAULT_REPO_DIR}}"
  [[ -n "${REPO_URL}" ]] || fail "Not inside the repo. Pass --repo-url so the script can clone it."

  if [[ -d "${REPO_DIR}/.git" ]]; then
    log "Updating existing repo in ${REPO_DIR}"
    git -C "${REPO_DIR}" fetch --all --prune
    git -C "${REPO_DIR}" checkout "${BRANCH}"
    git -C "${REPO_DIR}" pull --ff-only origin "${BRANCH}"
  else
    log "Cloning ${REPO_URL} into ${REPO_DIR}"
    ${SUDO} mkdir -p "$(dirname "${REPO_DIR}")"
    git clone --branch "${BRANCH}" "${REPO_URL}" "${REPO_DIR}"
  fi

  cd "${REPO_DIR}"
}

normalize_env_paths() {
  if [[ "${ENV_FILE}" != /* ]]; then
    ENV_FILE="${REPO_DIR}/${ENV_FILE}"
  fi
  if [[ "${RUNTIME_ENV_FILE}" != /* ]]; then
    RUNTIME_ENV_FILE="${REPO_DIR}/${RUNTIME_ENV_FILE}"
  fi
}

ensure_env_files() {
  [[ -f "${ENV_FILE}" ]] || fail "Missing env file: ${ENV_FILE}. Copy .env.prod.example and fill operator secrets first."
  touch "${RUNTIME_ENV_FILE}"
}

compose() {
  (
    cd "${REPO_DIR}"
    APP_ENV_FILE="${ENV_FILE}" \
    APP_RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE}" \
    ${SUDO} docker compose --env-file "${ENV_FILE}" -f docker-compose.yml -f docker-compose.prod.yml "$@"
  )
}

wait_for_service() {
  local service="$1"
  local timeout="${2:-240}"
  local start_ts
  start_ts="$(date +%s)"

  while true; do
    local container_id
    container_id="$(compose ps -q "${service}" | tail -n 1)"
    if [[ -n "${container_id}" ]]; then
      local status health
      status="$(${SUDO} docker inspect --format '{{.State.Status}}' "${container_id}")"
      health="$(${SUDO} docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "${container_id}")"
      if [[ "${status}" == "running" && ( "${health}" == "healthy" || "${health}" == "none" ) ]]; then
        log "Service healthy: ${service} (${status}/${health})"
        return
      fi
    fi

    if (( "$(date +%s)" - start_ts > timeout )); then
      compose ps
      compose logs --tail=120 "${service}" || true
      fail "Service did not become healthy in time: ${service}"
    fi
    sleep 5
  done
}

run_internal_smoke() {
  log "Running internal smoke checks"
  compose exec -T web python - <<'PY'
import sys
import urllib.request

for path in ("/health", "/login", "/register"):
    with urllib.request.urlopen(f"http://127.0.0.1:8000{path}", timeout=10) as response:
        status = getattr(response, "status", response.getcode())
        if status != 200:
            raise SystemExit(f"{path} returned {status}")
        print(f"OK {path} -> {status}")
PY
}

run_public_smoke_if_resolvable() {
  local public_app_url host
  public_app_url="$(awk -F= '/^PUBLIC_APP_URL=/{print $2}' "${ENV_FILE}" | tail -n 1)"
  if [[ -z "${public_app_url}" ]]; then
    log "PUBLIC_APP_URL not set; skipping public smoke"
    return
  fi
  host="${public_app_url#https://}"
  host="${host#http://}"
  host="${host%%/*}"
  if ! getent hosts "${host}" >/dev/null 2>&1; then
    log "Public host does not resolve yet (${host}); skipping external smoke for now"
    return
  fi

  log "Running public smoke against ${public_app_url}"
  for path in /health /login /register; do
    curl -fsS "${public_app_url}${path}" >/dev/null
    log "Public smoke OK: ${public_app_url}${path}"
  done
}

main() {
  log "Starting Hetzner deploy preparation"

  if [[ "${SKIP_INSTALL}" -eq 0 ]]; then
    ensure_base_packages
    ensure_docker
  fi

  resolve_repo
  normalize_env_paths
  ensure_env_files

  log "Validating Docker compose configuration"
  python3 "${REPO_DIR}/scripts/validate_prod_env.py" "${ENV_FILE}"
  compose config >/dev/null

  log "Building production images"
  compose build

  log "Starting stateful dependencies first"
  compose up -d postgres redis

  for service in postgres redis; do
    wait_for_service "${service}"
  done

  log "Running migrations/bootstrap"
  compose run --rm web python -m scripts.migrate

  log "Starting application services"
  compose up -d web worker scheduler bot listener caddy

  for service in web worker scheduler bot listener caddy; do
    wait_for_service "${service}"
  done

  if [[ "${RUN_SMOKE}" -eq 1 ]]; then
    run_internal_smoke
    run_public_smoke_if_resolvable
  fi

  log "Final compose status"
  compose ps
  log "Deploy script completed successfully"
}

main "$@"
