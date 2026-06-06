#!/usr/bin/env bash
set -Eeuo pipefail

SERVICE_PROFILE="${SERVICE_PROFILE:-service-access}"
GENERATE_SECRETS=1
SECRET_ENV_FILE="${TSW_INSTALL_ENV_FILE:-.tiny-swarm-world/local/live-installation.env}"
RESET_CONFIRMATION="RESET_TINY_SWARM_PLATFORM"

REQUIRED_SECRETS=(
  TSW_PORTAINER_PASSWORD
  TSW_NEXUS_ADMIN_PASSWORD
  TSW_JENKINS_ADMIN_PASSWORD
  TSW_RABBITMQ_PASSWORD
  TSW_SONARQUBE_ADMIN_PASSWORD
  TSW_POSTGRES_PASSWORD
  TSW_VAULTWARDEN_ADMIN_TOKEN
)

usage() {
  cat <<'EOF'
Tiny Swarm World live installation wrapper.

Usage:
  ./install.sh [--service-profile NAME] [--no-generate-secrets]

Options:
  --service-profile NAME   Service profile passed to setup run (default: service-access).
  --no-generate-secrets    Fail if required TSW_* secrets are missing.
  -h, --help               Show this help.

The script is Linux/WSL-only. It writes evidence under:
  .tiny-swarm-world/evidence/installation-tests/wsl2/<UTC timestamp>/

It runs the governed reset command before the canonical live setup command:
  PYTHONPATH=src python3 -m tiny_swarm_world platform reset --live --confirm RESET_TINY_SWARM_PLATFORM
  PYTHONPATH=src python3 -m tiny_swarm_world setup run --live

Generated local secret values include TSW_VAULTWARDEN_ADMIN_TOKEN. The
TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET variable is only an optional Swarm secret
name override; when omitted, setup uses tsw_vaultwarden_admin_token.
EOF
}

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

warn() {
  printf 'WARN: %s\n' "$*" >&2
}

require_command() {
  local command_name="$1"
  command -v "$command_name" >/dev/null 2>&1 || fail "Required command '$command_name' is not available."
}

shell_quote() {
  local value="$1"
  printf "'%s'" "${value//\'/\'\\\'\'}"
}

generate_secret_exports() {
  python3 - "$@" <<'PY'
import secrets
import sys

for name in sys.argv[1:]:
    print(f"export {name}='{secrets.token_urlsafe(32)}'")
PY
}

load_secret_env_file() {
  if [[ -f "$SECRET_ENV_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$SECRET_ENV_FILE"
  fi
}

write_context() {
  local evidence_dir="$1"
  local run_id="$2"
  local secrets_generated_count="$3"

  {
    printf 'run_id=%s\n' "$run_id"
    printf 'started_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'repo=%s\n' "$(pwd)"
    printf 'git_branch=%s\n' "$(git branch --show-current 2>/dev/null || true)"
    printf 'git_head=%s\n' "$(git rev-parse --short HEAD 2>/dev/null || true)"
    printf 'service_profile=%s\n' "$SERVICE_PROFILE"
    printf 'fresh_install_reset=required\n'
    printf 'secret_env_file=%s\n' "$SECRET_ENV_FILE"
    printf 'secrets_generated_count=%s\n' "$secrets_generated_count"
    printf 'platform_system=%s\n' "$(uname -s)"
    printf 'kernel_release=%s\n' "$(uname -r)"
    printf 'proc_osrelease=%s\n' "$(cat /proc/sys/kernel/osrelease 2>/dev/null || true)"
    if [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
      printf 'wsl_distro_name_present=yes\n'
    else
      printf 'wsl_distro_name_present=no\n'
    fi
    if [[ -n "${WSL_INTEROP:-}" ]]; then
      printf 'wsl_interop_present=yes\n'
    else
      printf 'wsl_interop_present=no\n'
    fi
  } >"$evidence_dir/context.txt"
}

run_recorded_command() {
  local command_line="$1"
  local log_file="$2"

  { printf 'y\n'; sleep 86400; } | script -q -e -c "$command_line" "$log_file"
}

confirm_reset() {
  local answer=""

  printf 'Fresh install will reset configured Tiny Swarm World managed state.\n'
  printf 'Type %s to continue: ' "$RESET_CONFIRMATION"
  if ! IFS= read -r answer; then
    fail "Fresh-install reset confirmation was not provided."
  fi
  [[ "$answer" == "$RESET_CONFIRMATION" ]] || fail "Fresh-install reset confirmation did not match."
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --service-profile)
      [[ $# -ge 2 ]] || fail "--service-profile requires a value."
      SERVICE_PROFILE="$2"
      shift 2
      ;;
    --no-generate-secrets)
      GENERATE_SECRETS=0
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

case "$SERVICE_PROFILE" in
  default|service-access)
    ;;
  *)
    fail "Unsupported service profile '$SERVICE_PROFILE'. Expected 'service-access' or 'default'."
    ;;
esac

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

[[ "$(uname -s)" == "Linux" ]] || fail "Tiny Swarm World installation is supported only on Linux/WSL."
[[ -d src/tiny_swarm_world ]] || fail "Run this script from the Tiny Swarm World repository root."
require_command python3
require_command script

mkdir -p "$(dirname "$SECRET_ENV_FILE")"
touch "$SECRET_ENV_FILE"
chmod 600 "$SECRET_ENV_FILE"

load_secret_env_file

missing_secrets=()
for secret_name in "${REQUIRED_SECRETS[@]}"; do
  if [[ -z "${!secret_name:-}" ]]; then
    missing_secrets+=("$secret_name")
  fi
done

secrets_generated_count=0
if (( ${#missing_secrets[@]} > 0 )); then
  if (( GENERATE_SECRETS == 0 )); then
    printf 'Missing required secrets:\n' >&2
    printf '  %s\n' "${missing_secrets[@]}" >&2
    fail "Provide the missing values in $SECRET_ENV_FILE or remove --no-generate-secrets."
  fi

  {
    printf '\n# Generated by install.sh at %s UTC\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    generate_secret_exports "${missing_secrets[@]}"
  } >>"$SECRET_ENV_FILE"
  chmod 600 "$SECRET_ENV_FILE"
  secrets_generated_count="${#missing_secrets[@]}"
  load_secret_env_file
fi

for secret_name in "${REQUIRED_SECRETS[@]}"; do
  export "$secret_name=${!secret_name}"
done
if [[ -n "${TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET:-}" ]]; then
  export TSW_VAULTWARDEN_ADMIN_TOKEN_SECRET
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1 && \
  ! git check-ignore -q .tiny-swarm-world/ >/dev/null 2>&1; then
  warn ".tiny-swarm-world/ is not ignored by git; do not commit local evidence or generated secrets."
fi

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
EVIDENCE_DIR=".tiny-swarm-world/evidence/installation-tests/wsl2/$RUN_ID"
mkdir -p "$EVIDENCE_DIR"
write_context "$EVIDENCE_DIR" "$RUN_ID" "$secrets_generated_count"

cat <<EOF
Tiny Swarm World live installation

Repository:      $(pwd)
Service profile: $SERVICE_PROFILE
Evidence:        $EVIDENCE_DIR
Secret file:     $SECRET_ENV_FILE

This will run live infrastructure automation. It may create or change VMs,
Docker resources, local service state, networks, and deployment artifacts.
Fresh install starts by resetting configured Tiny Swarm World managed state.
EOF

confirm_reset
printf 'reset_confirmation_present=yes\n' >>"$EVIDENCE_DIR/context.txt"

reset_command="PYTHONPATH=src python3 -m tiny_swarm_world platform reset --live --confirm $RESET_CONFIRMATION --service-profile $(shell_quote "$SERVICE_PROFILE")"
setup_command="PYTHONPATH=src python3 -m tiny_swarm_world setup run --live --service-profile $(shell_quote "$SERVICE_PROFILE")"

printf 'Starting fresh-install reset. Terminal UI is visible and recorded at: %s/reset-run.log\n' "$EVIDENCE_DIR"
set +e
run_recorded_command "$reset_command" "$EVIDENCE_DIR/reset-run.log"
reset_exit=$?
set -e

printf '%s\n' "$reset_exit" >"$EVIDENCE_DIR/reset-run.exit"
printf 'reset_exit=%s\n' "$reset_exit" >>"$EVIDENCE_DIR/context.txt"

if (( reset_exit != 0 )); then
  printf 'Fresh-install reset failed with exit code %s. Setup will not start.\n' "$reset_exit" >&2
  printf 'Evidence directory: %s\n' "$EVIDENCE_DIR" >&2
  printf 'setup_skipped_due_to_reset_failure=yes\n' >>"$EVIDENCE_DIR/context.txt"
  printf 'finished_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >>"$EVIDENCE_DIR/context.txt"
  printf '\nLast reset log lines:\n' >&2
  tail -n 80 "$EVIDENCE_DIR/reset-run.log" >&2 || true
  exit "$reset_exit"
fi

printf 'Starting live setup. Terminal UI is visible and recorded at: %s/setup-run.log\n' "$EVIDENCE_DIR"
set +e
run_recorded_command "$setup_command" "$EVIDENCE_DIR/setup-run.log"
setup_exit=$?
set -e

printf '%s\n' "$setup_exit" >"$EVIDENCE_DIR/setup-run.exit"
printf 'setup_exit=%s\n' "$setup_exit" >>"$EVIDENCE_DIR/context.txt"
printf 'finished_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >>"$EVIDENCE_DIR/context.txt"

if (( setup_exit == 0 )); then
  printf 'Installation completed successfully.\n'
  printf 'Evidence directory: %s\n' "$EVIDENCE_DIR"
else
  printf 'Installation failed with exit code %s.\n' "$setup_exit" >&2
  printf 'Evidence directory: %s\n' "$EVIDENCE_DIR" >&2
  printf '\nLast log lines:\n' >&2
  tail -n 80 "$EVIDENCE_DIR/setup-run.log" >&2 || true
fi

exit "$setup_exit"
