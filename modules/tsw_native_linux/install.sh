#!/usr/bin/env bash
# Native Linux compatibility entry point; shared execution belongs to tsw_core.
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/../../modules/tsw_core/bootstrap/linux/install.sh" "$@"
