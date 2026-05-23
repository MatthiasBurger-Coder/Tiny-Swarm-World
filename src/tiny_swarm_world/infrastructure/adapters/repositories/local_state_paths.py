from __future__ import annotations

from pathlib import Path

from tiny_swarm_world.infrastructure.project_paths import repository_root


LOCAL_STATE_DIRECTORY = ".tiny-swarm-world"


class LocalStatePathError(ValueError):
    """Raised when a local state path would escape the ignored state root."""


def local_state_file(
    *,
    root: Path | None = None,
    relative_path: str | Path,
) -> Path:
    repository = _repository_root(root)
    if _contains_infra_config_segment(repository):
        raise LocalStatePathError("repository root must not be infra/config")

    local_state_root = (repository / LOCAL_STATE_DIRECTORY).resolve()
    _require_within(local_state_root, repository, "local state root")
    if _contains_infra_config_segment(local_state_root):
        raise LocalStatePathError("local state root must not be under infra/config")

    requested = Path(relative_path)
    if requested.is_absolute():
        raise LocalStatePathError("local state paths must be repository-relative")

    resolved = (local_state_root / requested).resolve()
    _require_within(resolved, local_state_root, "local state file")
    if _contains_infra_config_segment(resolved):
        raise LocalStatePathError("observed state must not be stored under infra/config")
    return resolved


def _repository_root(root: Path | None) -> Path:
    if root is not None:
        return root.expanduser().resolve()
    return repository_root().resolve()


def _require_within(path: Path, root: Path, description: str) -> None:
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise LocalStatePathError(f"{description} escapes the repository root") from exc


def _contains_infra_config_segment(path: Path) -> bool:
    parts = tuple(part.lower() for part in path.parts)
    return any(
        part == "infra" and index + 1 < len(parts) and parts[index + 1] == "config"
        for index, part in enumerate(parts)
    )
