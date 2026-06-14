#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
  PYTHONPATH=src python3 -m tiny_swarm_world.installer --help
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

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

[[ "$(uname -s)" == "Linux" ]] || fail "Tiny Swarm World installation is supported only on Linux/WSL."
[[ -d src/tiny_swarm_world ]] || fail "Run this script from the Tiny Swarm World repository root."
command -v python3 >/dev/null 2>&1 || fail "Required command 'python3' is not available."

export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}src"
exec python3 -m tiny_swarm_world.installer "$@"
