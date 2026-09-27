#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ "$(uname -s)" != "Linux" ]]; then
  printf 'ERROR: Native Linux is required for prepare_linux.sh.\n' >&2
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  printf 'ERROR: Python 3.12 or newer is required. Install it manually on Ubuntu 24.04 or 26.04, then rerun prepare_linux.sh.\n' >&2
  exit 1
fi
if ! python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 12))'; then
  printf 'ERROR: Python 3.12 or newer is required for prepare_linux.sh.\n' >&2
  exit 1
fi

export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}src"
export PYTHONDONTWRITEBYTECODE=1
exec python3 -m tiny_swarm_world.prepare_linux "$@"
