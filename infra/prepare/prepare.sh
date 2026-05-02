#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$INFRA_ROOT/utils.sh"
source "$SCRIPT_DIR/portainer/prepare.sh"
#progress_bar 15
#source "$SCRIPT_DIR/nexus/prepare.sh"
