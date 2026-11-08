#!/usr/bin/env bash
set -Eeuo pipefail

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../../.."

[[ "$(uname -s)" == "Linux" ]] || fail "Tiny Swarm World commands are supported only on Linux/WSL."
[[ -d modules/tsw_core/src ]] || fail "Run this script from the Tiny Swarm World repository root."
command -v python3 >/dev/null 2>&1 || fail "Required command 'python3' is not available."

export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}."
exec python3 -m modules.tsw_core.src "$@"
