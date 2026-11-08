#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../../../.."

installer_module="tiny_swarm_world.simple_installer"

usage() {
  PYTHONPATH=modules/tsw_core/src python3 -m "$installer_module" --help
}

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

case "${1:-}" in
  -h|--help)
    usage
    exit 0
    ;;
  *)
    ;;
esac

[[ "$(uname -s)" == "Linux" ]] || fail "Tiny Swarm World installation is supported only on Linux/WSL."
[[ -d modules/tsw_core/src/tiny_swarm_world ]] || fail "Run this script from the Tiny Swarm World repository root."
command -v python3 >/dev/null 2>&1 || fail "Required command 'python3' is not available."

export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}modules/tsw_core/src"
export PYTHONDONTWRITEBYTECODE=1
exec python3 -m "$installer_module" "$@"
