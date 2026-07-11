from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from tiny_swarm_world.application.ports.repositories.port_routing_evidence_repository import (
    EffectiveAccessModelEvidence,
    PortRoutingEvidenceRepository,
)
from tiny_swarm_world.infrastructure.adapters.repositories.local_state_paths import (
    local_state_file,
)
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths


DEFAULT_ROUTING_EVIDENCE_PATH = (
    Path("evidence")
    / "solid-typed-evidence"
    / "routing"
    / "effective-access-model.json"
)


class RoutingEvidenceLocalRepository(PortRoutingEvidenceRepository):
    def __init__(
        self,
        root: Path | None = None,
        *,
        project_paths: ProjectPaths | None = None,
        relative_path: str | Path = DEFAULT_ROUTING_EVIDENCE_PATH,
    ):
        self.path = local_state_file(
            root=root,
            project_paths=project_paths,
            relative_path=relative_path,
        )

    def write_effective_access_model(self, evidence: EffectiveAccessModelEvidence) -> None:
        payload = json.dumps(
            evidence.to_dict(),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        ) + "\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        _set_private_mode(self.path.parent, 0o700)
        descriptor, temporary_name = tempfile.mkstemp(
            dir=self.path.parent,
            prefix=f".{self.path.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            _set_private_mode(temporary_path, 0o600)
            os.replace(temporary_path, self.path)
        except BaseException:
            try:
                os.close(descriptor)
            except OSError:
                pass
            temporary_path.unlink(missing_ok=True)
            raise


def _set_private_mode(path: Path, mode: int) -> None:
    try:
        path.chmod(mode)
    except NotImplementedError:
        return
