"""Repository-relative paths used by infrastructure adapters and tools."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    repository_root: Path
    source_root: Path
    infra_root: Path
    config_root: Path
    local_state_root: Path
    logs_root: Path

    @classmethod
    def from_roots(
        cls,
        repository_root: Path,
        infra_root: Path | None = None,
    ) -> "ProjectPaths":
        repository = repository_root.expanduser().resolve()
        infra = infra_root.expanduser().resolve() if infra_root else repository / "infra"
        local_state = repository / ".tiny-swarm-world"
        return cls(
            repository_root=repository,
            source_root=repository / "src",
            infra_root=infra,
            config_root=infra / "config",
            local_state_root=local_state,
            logs_root=local_state / "logs",
        )

    @classmethod
    def from_environment(cls) -> "ProjectPaths":
        repository = _configured_repository_root()
        infra = _configured_infra_root()
        return cls.from_roots(repository, infra)


def default_project_paths() -> ProjectPaths:
    return ProjectPaths.from_environment()


def repository_root() -> Path:
    return default_project_paths().repository_root


def source_root() -> Path:
    return default_project_paths().source_root


def infra_root() -> Path:
    return default_project_paths().infra_root


def config_root() -> Path:
    return default_project_paths().config_root


def local_state_root() -> Path:
    return default_project_paths().local_state_root


def logs_root() -> Path:
    return default_project_paths().logs_root


def _configured_repository_root() -> Path:
    configured_root = os.getenv("TSW_REPOSITORY_ROOT")
    if configured_root:
        return Path(configured_root).expanduser().resolve()

    for candidate in Path(__file__).resolve().parents:
        if (candidate / "infra").is_dir() and (candidate / "src").is_dir():
            return candidate

    raise RuntimeError("Could not locate the Tiny Swarm World repository root.")


def _configured_infra_root() -> Path | None:
    configured_root = os.getenv("TSW_INFRA_ROOT")
    if configured_root:
        return Path(configured_root).expanduser().resolve()
    return None
