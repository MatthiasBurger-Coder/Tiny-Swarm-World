"""Repository-relative paths used by infrastructure adapters and tools."""

from __future__ import annotations

import os
from pathlib import Path


def repository_root() -> Path:
    configured_root = os.getenv("TSW_REPOSITORY_ROOT")
    if configured_root:
        return Path(configured_root).expanduser().resolve()

    for candidate in Path(__file__).resolve().parents:
        if (candidate / "infra").is_dir() and (candidate / "src").is_dir():
            return candidate

    raise RuntimeError("Could not locate the Tiny Swarm World repository root.")


def source_root() -> Path:
    return repository_root() / "src"


def infra_root() -> Path:
    configured_root = os.getenv("TSW_INFRA_ROOT")
    if configured_root:
        return Path(configured_root).expanduser().resolve()
    return repository_root() / "infra"


def config_root() -> Path:
    return infra_root() / "config"


def local_state_root() -> Path:
    return repository_root() / ".tiny-swarm-world"


def logs_root() -> Path:
    return local_state_root() / "logs"
