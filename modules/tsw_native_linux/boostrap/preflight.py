"""Run Tiny Swarm World static preflight validation."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SOURCE_ROOT = REPOSITORY_ROOT / "modules/tsw_core/src"
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from modules.tsw_core.src.__main__ import main  # noqa: E402


if __name__ == "__main__":
    # Preserve the safe static default while allowing an explicitly requested
    # live preflight to use the same secure source/secret-path checks.
    raise SystemExit(asyncio.run(main(["--preflight", *sys.argv[1:]])))
