#!/usr/bin/env bash
# Shared core compatibility entry point.
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/../../modules/tsw_core/bootstrap/linux/install.sh" "$@"
