#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$SCRIPT_DIR/setup.py"
progress_bar 15
source "$SCRIPT_DIR/addMavenMirror.sh"
progress_bar 15
source "$SCRIPT_DIR/addLocalDockerRepository.sh"



