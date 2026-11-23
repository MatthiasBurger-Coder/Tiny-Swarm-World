#!/usr/bin/env bash
# Compose the existing host preparation and non-destructive installer commands.
set -Eeuo pipefail

usage() {
  printf '%s\n' \
    'Usage: ./setup_linux.sh [--help | --preflight | --dry-run | --resume] [--profile default|service-access|minimal|custom] [--services IDS] [--verbose]' \
    'Classic setup candidate for native Ubuntu 24.04/26.04 x86_64.' \
    'Default profile: service-access. Minimal and custom are available for read-only planning.' \
    'Custom requires comma-separated canonical service IDs. Requires Git, a trusted checkout and an ordinary user.' \
    'Preflight and preset dry-runs inspect readiness without writing configuration or evidence.' \
    'Apply requires an interactive terminal and separate preparation and install consent.' \
    'Use --resume with the original checkout and profile after interruption or restart.'
}

blocked() {
  printf 'BLOCKED: %s\n' "$1" >&2
  exit 2
}

mode=apply
profile=
services=
verbose=false
while (($#)); do
  case "$1" in
    -h|--help|--preflight|--dry-run|--resume)
      [[ "$mode" == apply ]] || blocked 'Choose one mode. See ./setup_linux.sh --help.'
      mode="$1"
      shift ;;
    --profile)
      [[ -z "$profile" ]] || blocked 'Specify at most one profile.'
      case "${2:-}" in
        default|service-access|minimal|custom) profile="$2" ;;
        *) blocked 'Choose default, service-access, minimal or custom.' ;;
      esac
      shift 2 ;;
    --services)
      [[ -z "$services" && -n "${2:-}" && "$2" != -* ]] ||
        blocked 'Supply one comma-separated list of canonical service IDs.'
      services="$2"
      shift 2 ;;
    --verbose) verbose=true; shift ;;
    *) blocked 'Unsupported argument. See ./setup_linux.sh --help.' ;;
  esac
done
if [[ "$profile" == custom ]]; then
  [[ -n "$services" ]] || blocked 'The custom profile requires --services.'
else
  [[ -z "$services" ]] || blocked '--services requires the custom profile.'
fi
if [[ "$mode" == -h || "$mode" == --help ]]; then
  usage
  exit 0
fi

kernel="$(uname -r)" || blocked 'Cannot identify the Linux kernel.'
[[ "$(uname -s)" == Linux && "$(uname -m)" == x86_64 && -n "$kernel" &&
   "${kernel,,}" != *microsoft* && "${kernel,,}" != *wsl* &&
   -z "${WSL_DISTRO_NAME:-}${WSL_INTEROP:-}" ]] || blocked 'Native Ubuntu x86_64 is required.'
proc_version="$(< /proc/version)" || blocked 'Cannot verify native Linux.'
[[ -n "$proc_version" && "${proc_version,,}" != *microsoft* ]] || blocked 'Native Ubuntu is required.'
(( EUID != 0 )) || blocked 'Run setup as an ordinary user. Individual preparation stages use sudo.'
if [[ ( "$mode" == apply || "$mode" == --resume ) && ( ! -t 0 || ! -t 1 ) ]]; then
  blocked 'Run guided setup in an interactive terminal. Use --dry-run for a preview.'
fi

cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
prepare=./modules/tsw_native_linux/boostrap/prepare_linux.sh
install=./install.sh
[[ -x "$prepare" && -x "$install" ]] || blocked 'Use a complete trusted Tiny Swarm World checkout.'
checkout="$(git rev-parse --show-toplevel 2>/dev/null)" && [[ "$checkout" == "$PWD" ]] ||
  blocked 'Use the root of a trusted Tiny Swarm World Git checkout with Git available.'
git rev-parse --verify HEAD >/dev/null 2>&1 || blocked 'Cannot identify the checkout revision.'
infra="$PWD/modules/tsw_core/infra"
[[ "${TSW_REPOSITORY_ROOT:-$PWD}" == "$PWD" && "${TSW_INFRA_ROOT:-$infra}" == "$infra" ]] ||
  blocked 'Use the checkout’s own repository and infrastructure paths, or use the advanced commands.'
export TSW_REPOSITORY_ROOT="$PWD" TSW_INFRA_ROOT="$infra"

if [[ "$profile" == minimal || "$profile" == custom ]]; then
  [[ "$mode" == --dry-run ]] ||
    blocked 'Use --dry-run to inspect this selection. Guided selective apply and host preflight require the selection-aware preparation handoff.'
  selection=(--selection-plan "$profile")
  if [[ -n "$services" ]]; then selection+=(--services="$services"); fi
  "$install" "${selection[@]}" || blocked 'Selection planning failed.'
  printf 'SELECTION_PLAN_READY. Host and service readiness are unverified.\n'
  exit 0
fi

profile="${profile:-service-access}"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.
if ! command -v python3 >/dev/null || ! python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 12))' >/dev/null 2>&1; then
  # The dependency-light interpreter stage owns its own checkpoint and consent.
  state="${XDG_STATE_HOME:-$HOME/.local/state}/tiny-swarm-world"
  [[ ! -e "$state/guided-setup" && ! -L "$state/guided-setup" ]] ||
    blocked 'Restore the required Python interpreter before opening the guided recovery checkpoint.'
  interpreter="$state/evidence/native-preparation/interpreter.state"
  args=(--service-profile "$profile")
  case "$mode" in
    --preflight|--dry-run) exec "$prepare" "$mode" "${args[@]}" ;;
    --resume)
      [[ -f "$interpreter" ]] || blocked 'No interpreter recovery checkpoint to resume.'
      result=0
      "$prepare" --dry-run "${args[@]}" || result=$?
      [[ "$result" == 2 ]] || blocked 'Recheck interpreter prerequisites before resuming.'
      ;;
    apply)
      [[ ! -e "$interpreter" && ! -L "$interpreter" ]] ||
        blocked 'Interpreter recovery evidence exists. Re-inventory with --dry-run, then use --resume.'
      ;;
  esac
  for capability in packages python incus network; do
    checkpoint="$state/bootstrap/$capability.state.json"
    [[ ! -e "$checkpoint" && ! -L "$checkpoint" ]] ||
      blocked 'Restore Python before validating the retained host preparation checkpoint.'
  done
  audit="$(timeout 15 dpkg --audit 2>&1)" && [[ -z "$audit" ]] ||
    blocked 'Package state requires operator review with dpkg --audit.'
  printf 'Preparation will request consent for each change. Run sudo -v in this terminal if needed.\n'
  source ./modules/tsw_native_linux/boostrap/ubuntu_python_prerequisites.sh
  result=0
  tsw_python_prerequisites "${args[@]}" || result=$?
  if (( result != 0 )); then
    outcome=PARTIAL code=1
    case "$result" in
      2) outcome=BLOCKED; code=2 ;;
      124) outcome=TIMEOUT; code=124 ;;
      130|143) outcome=INTERRUPTED; code=130 ;;
    esac
    printf '%s at interpreter preparation (child exit %s). Preserve protected evidence. Next: ./setup_linux.sh --profile %s --dry-run\n' \
      "$outcome" "$result" "$profile" >&2
    exit "$code"
  fi
  mode=apply
fi

exec python3 -m modules.tsw_core.src.infrastructure.adapters.guided_setup "$mode" "$profile" "$verbose"
