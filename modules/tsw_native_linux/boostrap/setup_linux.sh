#!/usr/bin/env bash
# Compose the existing host preparation and non-destructive installer commands.
set -Eeuo pipefail

usage() {
  printf '%s\n' \
    'Usage: ./setup_linux.sh [--help | --preflight | --dry-run] [--profile default|service-access] [--verbose]' \
    'Guided setup candidate for native Ubuntu 24.04/26.04 x86_64.' \
    'Default profile: service-access. Requires Git, a trusted checkout and an ordinary user.' \
    'Preflight and dry-run inspect readiness without writing configuration or evidence.' \
    'Apply requires an interactive terminal and separate preparation and install consent.'
}

blocked() {
  printf 'BLOCKED: %s\n' "$1" >&2
  exit 2
}

mode=apply
profile=
verbose=false
while (($#)); do
  case "$1" in
    -h|--help|--preflight|--dry-run)
      [[ "$mode" == apply ]] || blocked 'Choose one mode. See ./setup_linux.sh --help.'
      mode="$1"
      shift ;;
    --profile)
      [[ -z "$profile" ]] || blocked 'Specify at most one profile.'
      case "${2:-}" in
        default|service-access) profile="$2" ;;
        *) blocked 'Available setup profiles are default and service-access.' ;;
      esac
      shift 2 ;;
    --verbose) verbose=true; shift ;;
    *) blocked 'Unsupported argument. See ./setup_linux.sh --help.' ;;
  esac
done
if [[ "$mode" == -h || "$mode" == --help ]]; then
  usage
  exit 0
fi

stage_exit() {
  local stage="$1" child="$2" outcome=FAILED code=1 next="$rerun --dry-run"
  case "$child" in
    124) outcome=TIMEOUT; code=124 ;;
    130) outcome=INTERRUPTED; code=130 ;;
    *)
      case "$stage:$child" in
        prepare:2|preflight:2) outcome=BLOCKED; code=2 ;;
        prepare:3|preflight:3) outcome=RESTART_REQUIRED; code=3; next="$rerun" ;;
        prepare:4) outcome=PARTIAL ;;
      esac ;;
  esac
  printf '%s at %s (child exit %s). Next: %s\n' "$outcome" "$stage" "$child" "$next" >&2
  exit "$code"
}

run_stage() {
  active_stage="$1"
  shift
  if "$verbose"; then
    printf 'Setup stage: %s\n' "$active_stage" >&2
  fi
  "$@" || stage_exit "$active_stage" "$?"
}

kernel="$(uname -r)" || blocked 'Cannot identify the Linux kernel.'
[[ "$(uname -s)" == Linux && "$(uname -m)" == x86_64 && -n "$kernel" &&
   "${kernel,,}" != *microsoft* && "${kernel,,}" != *wsl* &&
   -z "${WSL_DISTRO_NAME:-}${WSL_INTEROP:-}" ]] || blocked 'Native Ubuntu x86_64 is required.'
proc_version="$(< /proc/version)" || blocked 'Cannot verify native Linux.'
[[ -n "$proc_version" && "${proc_version,,}" != *microsoft* ]] || blocked 'Native Ubuntu is required.'
(( EUID != 0 )) || blocked 'Run setup as an ordinary user. Individual preparation stages use sudo.'
if [[ "$mode" == apply && ( ! -t 0 || ! -t 1 ) ]]; then
  blocked 'Run guided setup in an interactive terminal. Use --dry-run for a preview.'
fi

cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
prepare=./modules/tsw_native_linux/boostrap/prepare_linux.sh
install=./install.sh
[[ -x "$prepare" && -x "$install" ]] || blocked 'Use a complete trusted Tiny Swarm World checkout.'
checkout="$(git rev-parse --show-toplevel 2>/dev/null)" && [[ "$checkout" == "$PWD" ]] ||
  blocked 'Use the root of a trusted Tiny Swarm World Git checkout with Git available.'
revision="$(git rev-parse --verify HEAD 2>/dev/null)" || blocked 'Cannot identify the checkout revision.'
infra="$PWD/modules/tsw_core/infra"
[[ "${TSW_REPOSITORY_ROOT:-$PWD}" == "$PWD" && "${TSW_INFRA_ROOT:-$infra}" == "$infra" ]] ||
  blocked 'Use the checkout’s own repository and infrastructure paths, or use the advanced commands.'
export TSW_REPOSITORY_ROOT="$PWD" TSW_INFRA_ROOT="$infra"

profile="${profile:-service-access}"
profile_args=(--service-profile "$profile")
printf -v rerun '%q --profile %q' "$PWD/setup_linux.sh" "$profile"
if "$verbose"; then rerun+=' --verbose'; fi
trap 'stage_exit "${active_stage:-preflight}" 130' INT

if [[ "$mode" != apply ]]; then
  run_stage preflight "$prepare" "$mode" "${profile_args[@]}"
  run_stage plan "$install" "$mode" "${profile_args[@]}"
  printf '%s: Host preparation and installer checks passed. Services have not been verified.\n' \
    "$( [[ "$mode" == --dry-run ]] && printf PLAN_READY || printf READY )"
  exit 0
fi

printf 'Setup profile: %s. Preparation will request consent for each change.\n' "$profile"
printf 'If a privileged stage needs authentication, run sudo -v in this terminal and retry.\n'
run_stage prepare "$prepare" "${profile_args[@]}"
printf 'Host preparation complete. Reviewing the installation plan.\n'
run_stage plan "$install" --dry-run "${profile_args[@]}"
active_stage=consent.install
printf 'Type yes to proceed to installation for profile %s at source %s: ' "$profile" "$revision" >&2
IFS= read -r answer && [[ "$answer" == yes ]] || blocked 'Installation consent missing. Rerun setup to review the plan again.'
[[ "$(git rev-parse --verify HEAD 2>/dev/null)" == "$revision" ]] ||
  blocked 'Checkout revision changed. Rerun setup to review the plan again.'
run_stage install "$install" "${profile_args[@]}"
printf 'INSTALLATION_COMPLETE: The installer finished successfully. Verify service access separately.\n'
