#!/usr/bin/env bash
# Native Linux entry point; the handoff belongs to the bootstrap module.
set -Eeuo pipefail
SCRIPT_DIR="$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/modules/tsw_native_linux/boostrap/setup_linux.sh" "$@"
