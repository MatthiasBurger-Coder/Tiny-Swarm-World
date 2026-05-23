"""Run Tiny Swarm World static preflight validation."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from tiny_swarm_world.__main__ import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(["--preflight"])))
