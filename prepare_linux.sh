#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
export PYTHONDONTWRITEBYTECODE=1
source "$SCRIPT_DIR/tools/ubuntu_python_prerequisites.sh"
if tsw_python_prerequisites "$@"; then
  :
else
  result=$?
  [[ "$result" == 10 ]] && exit 0
  exit "$result"
fi
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}src"
exec python3 -m tiny_swarm_world.prepare_linux "$@"
