#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd -- "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPOSITORY_ROOT"
export PYTHONDONTWRITEBYTECODE=1
source "$SCRIPT_DIR/ubuntu_python_prerequisites.sh"
if tsw_python_prerequisites "$@"; then
  :
else
  result=$?
  [[ "$result" == 10 ]] && exit 0
  exit "$result"
fi
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}."
exec python3 -m modules.tsw_core.src.prepare_linux "$@"
