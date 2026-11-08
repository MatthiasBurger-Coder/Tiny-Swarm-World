from __future__ import annotations

import os
import stat
from pathlib import Path

from tiny_swarm_world.application.ports.preflight.port_secret_storage_probe import (
    PortSecretStorageProbe,
)
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.preflight.secret_storage import SecretStorageInspection
from tiny_swarm_world.infrastructure.adapters.host.project_filesystem_inspector import (
    ProjectFilesystemInspector,
)


class SecretStorageProbe(PortSecretStorageProbe):
    """Read secret-path metadata without reading secret contents."""

    def __init__(self, filesystem_inspector: ProjectFilesystemInspector) -> None:
        self.filesystem_inspector = filesystem_inspector

    def effective_identity(self) -> tuple[int, int]:
        return os.geteuid(), os.getegid()

    def inspect(
        self,
        path: str,
        host_environment: HostEnvironmentKind,
    ) -> SecretStorageInspection:
        resolved = _resolve_path(path)
        parent = resolved.parent
        path_stat = _safe_stat(resolved)
        parent_stat = _safe_stat(parent)
        filesystem = self.filesystem_inspector.inspect(
            (resolved if path_stat is not None else parent).as_posix(),
            host_environment,
        )
        return SecretStorageInspection(
            resolved_path=resolved.as_posix(),
            filesystem_kind=filesystem.kind,
            filesystem_type=filesystem.filesystem_type,
            exists=path_stat is not None,
            is_regular_file=path_stat is not None and stat.S_ISREG(path_stat.st_mode),
            owner_uid=path_stat.st_uid if path_stat is not None else None,
            group_gid=path_stat.st_gid if path_stat is not None else None,
            mode=stat.S_IMODE(path_stat.st_mode) if path_stat is not None else None,
            parent_exists=parent_stat is not None and stat.S_ISDIR(parent_stat.st_mode),
            parent_owner_uid=parent_stat.st_uid if parent_stat is not None else None,
            parent_group_gid=parent_stat.st_gid if parent_stat is not None else None,
            parent_mode=(stat.S_IMODE(parent_stat.st_mode) if parent_stat is not None else None),
            classification_source=filesystem.classification_source,
        )


def _resolve_path(value: str) -> Path:
    try:
        return Path(value).expanduser().resolve(strict=False)
    except (OSError, RuntimeError):
        return Path(value).expanduser().absolute()


def _safe_stat(path: Path):
    try:
        return path.stat()
    except OSError:
        return None
