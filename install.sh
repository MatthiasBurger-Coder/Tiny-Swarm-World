#!/usr/bin/env bash
set -Eeuo pipefail

SERVICE_PROFILE="${SERVICE_PROFILE:-service-access}"
GENERATE_SECRETS=1
SECRET_ENV_FILE="${TSW_INSTALL_ENV_FILE:-.tiny-swarm-world/local/live-installation.env}"
INFISICAL_SECRET_ENV_FILE="${TSW_INFISICAL_SECRET_ENV_FILE:-.tiny-swarm/secrets/bootstrap.local.env}"
GENERATED_SECRET_ENV_FILE="${TSW_GENERATED_SECRET_ENV_FILE:-.tiny-swarm/secrets/generated.local.env}"
NATIVE_LINUX_VENV="${TSW_NATIVE_LINUX_VENV:-.tiny-swarm-world/install-venv}"
RESET_CONFIRMATION="RESET_TINY_SWARM_PLATFORM"
RESET_CONFIRMED_BY_FLAG=0
NON_INTERACTIVE_LIVE_APPROVAL=0

REQUIRED_SECRETS=(
  TSW_PORTAINER_ADMIN_PASSWORD
  TSW_NEXUS_ADMIN_PASSWORD
  TSW_JENKINS_ADMIN_PASSWORD
  TSW_RABBITMQ_PASSWORD
  TSW_SONARQUBE_ADMIN_PASSWORD
  TSW_POSTGRES_PASSWORD
  TSW_SONARQUBE_POSTGRES_PASSWORD
  TSW_INFISICAL_LOGIN_EMAIL
  TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD
  TSW_INFISICAL_ENCRYPTION_KEY
  TSW_INFISICAL_AUTH_SECRET
  TSW_INFISICAL_POSTGRES_PASSWORD
  TSW_INFISICAL_REDIS_PASSWORD
)

usage() {
  cat <<'EOF'
Tiny Swarm World live installation wrapper.

Usage:
  ./install.sh [--service-profile NAME] [--no-generate-secrets] [--confirm-reset] [--non-interactive-live-approval]

Options:
  --service-profile NAME   Service profile passed to setup run (default: service-access).
  --no-generate-secrets    Fail if required TSW_* secrets are missing.
  --confirm-reset          Confirm the governed fresh-install reset without prompting.
  --non-interactive-live-approval
                           Pass explicit non-interactive live approval to the CLI.
                           Without this flag, recorded live commands ask for the
                           CLI's interactive live confirmation.
  -h, --help               Show this help.

Optional environment:
  TSW_LXC_DOCKER_REGISTRY_MIRROR
      Docker registry mirror URL written into managed LXC nodes during Docker
      installation. Use an address reachable from inside the nodes, not
      127.0.0.1. If unset, a running local tiny-swarm-nexus-cache is detected
      and wired automatically when an LXC bridge address is available.
  TSW_SEED_INFISICAL_ITEMS
      Controls legacy Service Access credential inventory seeding. Defaults to
      0 because the Infisical silent-bootstrap greenpath must not automate
      browser/UI clicks.
The script is Linux/WSL-only. It writes evidence under:
  .tiny-swarm-world/evidence/installation-tests/<host-directory>/<UTC timestamp>/

Supported host directories:
  wsl2          WSL2 detected from WSL environment or kernel signals.
  native_linux  Native Linux when no WSL signal is present.

It runs the governed reset command before the canonical live setup command:
  PYTHONPATH=src python3 -m tiny_swarm_world platform reset --live --confirm RESET_TINY_SWARM_PLATFORM
  PYTHONPATH=src python3 -m tiny_swarm_world setup run --live

Generated local secret values include the Infisical admin login and platform
keys `TSW_INFISICAL_LOGIN_EMAIL`, `TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD`,
`TSW_INFISICAL_ENCRYPTION_KEY`, `TSW_INFISICAL_AUTH_SECRET`, and
`TSW_INFISICAL_POSTGRES_PASSWORD`. Infisical bootstrap values are mirrored to the
ignored .tiny-swarm/secrets/bootstrap.local.env file and generated project
secrets are kept in .tiny-swarm/secrets/generated.local.env for recovery.
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

is_wsl_environment() {
  if [[ -n "${WSL_DISTRO_NAME:-}" || -n "${WSL_INTEROP:-}" ]]; then
    return 0
  fi
  grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease /proc/version 2>/dev/null
}

host_runtime_type() {
  if is_wsl_environment; then
    printf 'wsl2\n'
  else
    printf 'native_linux\n'
  fi
}

host_detection_source() {
  if [[ -n "${WSL_DISTRO_NAME:-}" || -n "${WSL_INTEROP:-}" ]]; then
    printf 'wsl_environment\n'
  elif grep -qiE 'microsoft|wsl' /proc/sys/kernel/osrelease /proc/version 2>/dev/null; then
    printf 'kernel_signal\n'
  else
    printf 'uname_linux_without_wsl_signal\n'
  fi
}

python_imports_available() {
  local python_bin="$1"
  "$python_bin" - <<'PY' >/dev/null 2>&1
import pydantic
import requests
import ruamel.yaml
import yaml
PY
}

ensure_native_linux_python_environment() {
  local python_bin="python3"

  if is_wsl_environment; then
    printf '%s\n' "$python_bin"
    return
  fi

  if (( ${TSW_INSTALL_SKIP_NATIVE_DEPENDENCY_BOOTSTRAP:-0} == 1 )); then
    printf '%s\n' "$python_bin"
    return
  fi

  if python_imports_available "$python_bin"; then
    printf '%s\n' "$python_bin"
    return
  fi
  if [[ -x "$NATIVE_LINUX_VENV/bin/python" ]] && \
    python_imports_available "$NATIVE_LINUX_VENV/bin/python"; then
    printf '%s\n' "$NATIVE_LINUX_VENV/bin/python"
    return
  fi

  printf 'Native Linux Python dependencies are missing; preparing %s.\n' "$NATIVE_LINUX_VENV" >&2
  "$python_bin" -m venv "$NATIVE_LINUX_VENV" || fail \
    "Could not create native Linux virtual environment at $NATIVE_LINUX_VENV. Install python3-venv and rerun install.sh."
  "$NATIVE_LINUX_VENV/bin/python" -m pip install --upgrade pip >&2
  "$NATIVE_LINUX_VENV/bin/python" -m pip install -r requirements.txt >&2

  python_imports_available "$NATIVE_LINUX_VENV/bin/python" || fail \
    "Native Linux Python dependency bootstrap did not make required modules importable."
  printf '%s\n' "$NATIVE_LINUX_VENV/bin/python"
}

shell_quote() {
  local value="$1"
  printf "'%s'" "${value//\'/\'\\\'\'}"
}

write_export() {
  local name="$1"
  local value="$2"
  printf 'export %s=%s\n' "$name" "$(shell_quote "$value")"
}

generate_secret_exports() {
  python3 - "$@" <<'PY'
import shlex
import secrets
import sys

for name in sys.argv[1:]:
    if name == "TSW_INFISICAL_ENCRYPTION_KEY":
        value = secrets.token_hex(16)
    elif name == "TSW_INFISICAL_LOGIN_EMAIL":
        value = "admin@tiny-swarm-world.local"
    elif name == "TSW_SONARQUBE_ADMIN_PASSWORD":
        value = f"{secrets.token_urlsafe(32)}!"
    else:
        value = secrets.token_urlsafe(32)
    print(f"export {name}={shlex.quote(value)}")
PY
}

sonarqube_password_is_valid() {
  local value="$1"
  [[ ${#value} -ge 12 && "$value" =~ [\!\@\#\$\%\^\&\*\(\)_\+] ]]
}

load_secret_env_file() {
  if [[ -f "$SECRET_ENV_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$SECRET_ENV_FILE"
  fi
  if [[ -f "$INFISICAL_SECRET_ENV_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$INFISICAL_SECRET_ENV_FILE"
  fi
}

write_infisical_secret_file() {
  mkdir -p "$(dirname "$INFISICAL_SECRET_ENV_FILE")"
  {
    printf '# Generated by install.sh. Do not commit.\n'
    write_export TSW_INFISICAL_ENCRYPTION_KEY "$TSW_INFISICAL_ENCRYPTION_KEY"
    write_export TSW_INFISICAL_AUTH_SECRET "$TSW_INFISICAL_AUTH_SECRET"
    write_export TSW_INFISICAL_POSTGRES_PASSWORD "$TSW_INFISICAL_POSTGRES_PASSWORD"
    write_export TSW_INFISICAL_REDIS_PASSWORD "$TSW_INFISICAL_REDIS_PASSWORD"
    write_export TSW_INFISICAL_LOGIN_EMAIL "$TSW_INFISICAL_LOGIN_EMAIL"
    write_export TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD "$TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD"
    write_export ENCRYPTION_KEY "$TSW_INFISICAL_ENCRYPTION_KEY"
    write_export AUTH_SECRET "$TSW_INFISICAL_AUTH_SECRET"
    write_export POSTGRES_PASSWORD "$TSW_INFISICAL_POSTGRES_PASSWORD"
    write_export REDIS_PASSWORD "$TSW_INFISICAL_REDIS_PASSWORD"
    write_export INITIAL_BOOTSTRAP_ADMIN_PASSWORD "$TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD"
  } >"$INFISICAL_SECRET_ENV_FILE"
  chmod 600 "$INFISICAL_SECRET_ENV_FILE"
}

ensure_default_config_exports() {
  local updated=0

  if [[ -z "${TSW_TRAEFIK_TLS_CERT_SECRET_NAME:-}" ]]; then
    TSW_TRAEFIK_TLS_CERT_SECRET_NAME="tsw_traefik_tls_cert"
    updated=1
  fi
  if [[ -z "${TSW_TRAEFIK_TLS_KEY_SECRET_NAME:-}" ]]; then
    TSW_TRAEFIK_TLS_KEY_SECRET_NAME="tsw_traefik_tls_key"
    updated=1
  fi

  if (( updated == 1 )); then
    {
      printf '\n# Default non-secret config values written by install.sh at %s UTC\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      write_export TSW_TRAEFIK_TLS_CERT_SECRET_NAME "$TSW_TRAEFIK_TLS_CERT_SECRET_NAME"
      write_export TSW_TRAEFIK_TLS_KEY_SECRET_NAME "$TSW_TRAEFIK_TLS_KEY_SECRET_NAME"
    } >>"$SECRET_ENV_FILE"
    chmod 600 "$SECRET_ENV_FILE"
  fi
}

ensure_sonarqube_password_policy() {
  if sonarqube_password_is_valid "${TSW_SONARQUBE_ADMIN_PASSWORD:-}"; then
    return 0
  fi

  if (( GENERATE_SECRETS == 0 )); then
    fail "TSW_SONARQUBE_ADMIN_PASSWORD must be at least 12 characters and contain a special character."
  fi

  TSW_SONARQUBE_ADMIN_PASSWORD="$(
    generate_secret_exports TSW_SONARQUBE_ADMIN_PASSWORD |
      sed -n "s/^export TSW_SONARQUBE_ADMIN_PASSWORD='\\(.*\\)'$/\\1/p"
  )"
  {
    printf '\n# Regenerated by install.sh for SonarQube password policy at %s UTC\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    write_export TSW_SONARQUBE_ADMIN_PASSWORD "$TSW_SONARQUBE_ADMIN_PASSWORD"
  } >>"$SECRET_ENV_FILE"
  {
    printf '\n# Regenerated by install.sh for SonarQube password policy at %s UTC\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    write_export TSW_SONARQUBE_ADMIN_PASSWORD "$TSW_SONARQUBE_ADMIN_PASSWORD"
  } >>"$GENERATED_SECRET_ENV_FILE"
  chmod 600 "$SECRET_ENV_FILE" "$GENERATED_SECRET_ENV_FILE"
}

write_context() {
  local evidence_dir="$1"
  local run_id="$2"
  local secrets_generated_count="$3"
  local resolved_host_type="$4"
  local detection_source="$5"
  local live_execution_mode="$6"
  local live_approval_source="$7"

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
    printf 'host_runtime_type=%s\n' "$resolved_host_type"
    printf 'host_runtime_detection_source=%s\n' "$detection_source"
    printf 'selected_evidence_directory=%s\n' "$evidence_dir"
    printf 'live_execution_mode=%s\n' "$live_execution_mode"
    printf 'live_approval_source=%s\n' "$live_approval_source"
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
  local effective_command="$command_line"

  if [[ -n "${TSW_INSTALL_COMMAND_GROUP:-}" ]]; then
    effective_command="sg ${TSW_INSTALL_COMMAND_GROUP} -c $(shell_quote "$command_line")"
  fi

  script -q -e -c "$effective_command" "$log_file"
}

configure_native_linux_command_group() {
  if is_wsl_environment; then
    return
  fi
  if (( ${TSW_INSTALL_SKIP_NATIVE_GROUP_SWITCH:-0} == 1 )); then
    return
  fi
  if ! command -v sg >/dev/null 2>&1 || ! command -v lxc >/dev/null 2>&1; then
    return
  fi
  if id -nG | tr ' ' '\n' | grep -qx 'lxd'; then
    return
  fi
  if getent group lxd | awk -F: -v user="$(id -un)" '
    $1 == "lxd" {
      split($4, members, ",")
      for (member_index in members) {
        if (members[member_index] == user) {
          found = 1
        }
      }
    }
    END { exit found ? 0 : 1 }
  '; then
    TSW_INSTALL_COMMAND_GROUP="lxd"
    export TSW_INSTALL_COMMAND_GROUP
    printf 'Native Linux LXD group membership exists but is not active; running live commands through sg lxd.\n' >&2
  fi
}

confirm_reset() {
  local answer=""

  if (( RESET_CONFIRMED_BY_FLAG == 1 )); then
    printf 'Fresh-install reset confirmed by explicit --confirm-reset flag.\n'
    return
  fi

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
    --confirm-reset)
      RESET_CONFIRMED_BY_FLAG=1
      shift
      ;;
    --non-interactive-live-approval)
      NON_INTERACTIVE_LIVE_APPROVAL=1
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

PYTHON_BIN="$(ensure_native_linux_python_environment)"
configure_native_linux_command_group

mkdir -p "$(dirname "$SECRET_ENV_FILE")"
touch "$SECRET_ENV_FILE"
chmod 600 "$SECRET_ENV_FILE"
mkdir -p "$(dirname "$INFISICAL_SECRET_ENV_FILE")"
touch "$INFISICAL_SECRET_ENV_FILE"
chmod 600 "$INFISICAL_SECRET_ENV_FILE"
mkdir -p "$(dirname "$GENERATED_SECRET_ENV_FILE")"
touch "$GENERATED_SECRET_ENV_FILE"
chmod 600 "$GENERATED_SECRET_ENV_FILE"

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

ensure_sonarqube_password_policy
ensure_default_config_exports

for secret_name in "${REQUIRED_SECRETS[@]}"; do
  export "$secret_name=${!secret_name}"
done
export TSW_TRAEFIK_TLS_CERT_SECRET_NAME
export TSW_TRAEFIK_TLS_KEY_SECRET_NAME
write_infisical_secret_file
if [[ -z "${TSW_SEED_INFISICAL_ITEMS:-}" ]]; then
  TSW_SEED_INFISICAL_ITEMS=0
fi
export TSW_SEED_INFISICAL_ITEMS
if [[ -n "${TSW_LXC_DOCKER_REGISTRY_MIRROR:-}" ]]; then
  export TSW_LXC_DOCKER_REGISTRY_MIRROR
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1 && \
  ! git check-ignore -q .tiny-swarm-world/ >/dev/null 2>&1; then
  warn ".tiny-swarm-world/ is not ignored by git; do not commit local evidence or generated secrets."
fi

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)"
RESOLVED_HOST_TYPE="$(host_runtime_type)"
HOST_DETECTION_SOURCE="$(host_detection_source)"
if (( NON_INTERACTIVE_LIVE_APPROVAL == 1 )); then
  LIVE_EXECUTION_MODE="non_interactive"
  LIVE_APPROVAL_SOURCE="explicit_automation_flag"
  LIVE_APPROVAL_ARGUMENT=" --approve-live"
else
  LIVE_EXECUTION_MODE="interactive"
  LIVE_APPROVAL_SOURCE="operator_prompt"
  LIVE_APPROVAL_ARGUMENT=""
fi
EVIDENCE_DIR=".tiny-swarm-world/evidence/installation-tests/$RESOLVED_HOST_TYPE/$RUN_ID"
mkdir -p "$EVIDENCE_DIR"
write_context \
  "$EVIDENCE_DIR" \
  "$RUN_ID" \
  "$secrets_generated_count" \
  "$RESOLVED_HOST_TYPE" \
  "$HOST_DETECTION_SOURCE" \
  "$LIVE_EXECUTION_MODE" \
  "$LIVE_APPROVAL_SOURCE"

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
if (( RESET_CONFIRMED_BY_FLAG == 1 )); then
  printf 'reset_confirmation_source=explicit_flag\n' >>"$EVIDENCE_DIR/context.txt"
else
  printf 'reset_confirmation_source=interactive_prompt\n' >>"$EVIDENCE_DIR/context.txt"
fi

reset_command="PYTHONPATH=src $(shell_quote "$PYTHON_BIN") -m tiny_swarm_world platform reset --live${LIVE_APPROVAL_ARGUMENT} --confirm $RESET_CONFIRMATION --service-profile $(shell_quote "$SERVICE_PROFILE")"
setup_command="PYTHONPATH=src $(shell_quote "$PYTHON_BIN") -m tiny_swarm_world setup run --live${LIVE_APPROVAL_ARGUMENT} --service-profile $(shell_quote "$SERVICE_PROFILE")"

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
