from __future__ import annotations

import json
import os
import stat
import tempfile
from collections.abc import Mapping
from pathlib import Path

from tiny_swarm_world.application.ports.host.port_project_filesystem_inspector import (
    PortProjectFilesystemInspector,
)
from tiny_swarm_world.application.ports.repositories.port_project_filesystem_evidence_repository import (
    PortProjectFilesystemEvidenceRepository,
    ProjectFilesystemEvidenceError,
)
from tiny_swarm_world.domain.project_filesystem import (
    ProjectFilesystemAssessment,
    ProjectFilesystemKind,
)

_RELATIVE_EVIDENCE_PATH = (
    Path("tiny-swarm-world")
    / "installation"
    / "project-filesystem-decision.json"
)


class ProjectFilesystemEvidenceLocalRepository(
    PortProjectFilesystemEvidenceRepository
):
    def __init__(
        self,
        *,
        path: Path,
        target_inspector: PortProjectFilesystemInspector,
    ) -> None:
        self.path = path.expanduser()
        self.target_inspector = target_inspector

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str],
        *,
        target_inspector: PortProjectFilesystemInspector,
    ) -> "ProjectFilesystemEvidenceLocalRepository":
        configured = environment.get("XDG_STATE_HOME", "").strip()
        if configured:
            state_root = Path(configured).expanduser()
        else:
            home = environment.get("HOME", "").strip()
            state_root = (
                Path(home).expanduser() if home else Path.home()
            ) / ".local" / "state"
        return cls(
            path=state_root / _RELATIVE_EVIDENCE_PATH,
            target_inspector=target_inspector,
        )

    def write(self, assessment: ProjectFilesystemAssessment) -> None:
        if not self.path.is_absolute():
            raise ProjectFilesystemEvidenceError(
                "XDG_STATE_HOME must be an absolute Linux path."
            )
        target = self.target_inspector.inspect(
            self.path.parent.as_posix(),
            assessment.host_environment,
        )
        if target.kind not in {
            ProjectFilesystemKind.NATIVE_LINUX,
            ProjectFilesystemKind.WSL_LINUX,
        }:
            raise ProjectFilesystemEvidenceError(
                "Protected evidence target is not a verified Linux-native filesystem."
            )
        payload = json.dumps(
            assessment.to_protected_evidence_dict(),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        ) + "\n"
        temporary_path: Path | None = None
        descriptor = -1
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            _set_private_mode(self.path.parent, 0o700)
            descriptor, temporary_name = tempfile.mkstemp(
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
            )
            temporary_path = Path(temporary_name)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                descriptor = -1
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            _set_private_mode(temporary_path, 0o600)
            os.replace(temporary_path, self.path)
            temporary_path = None
            _set_private_mode(self.path, 0o600)
            _sync_directory(self.path.parent)
        except ProjectFilesystemEvidenceError:
            raise
        except (OSError, ValueError) as error:
            raise ProjectFilesystemEvidenceError(
                "Protected project-filesystem evidence could not be stored."
            ) from error
        finally:
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)


def _set_private_mode(path: Path, mode: int) -> None:
    try:
        path.chmod(mode)
        actual = stat.S_IMODE(path.stat().st_mode)
    except OSError as error:
        raise ProjectFilesystemEvidenceError(
            "Protected evidence permissions could not be enforced."
        ) from error
    if actual != mode:
        raise ProjectFilesystemEvidenceError(
            "Protected evidence permissions do not match the required owner-only mode."
        )


def _sync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        return
    finally:
        os.close(descriptor)
