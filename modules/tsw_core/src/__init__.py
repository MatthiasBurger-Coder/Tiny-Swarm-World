"""Tiny Swarm World runtime package."""

import sys

# Repository bootstrap runs before an editable installation exists.
sys.modules.setdefault("tiny_swarm_world", sys.modules[__name__])
