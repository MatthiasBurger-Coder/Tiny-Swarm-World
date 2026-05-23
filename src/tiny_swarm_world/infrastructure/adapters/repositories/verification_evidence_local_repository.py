from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tiny_swarm_world.application.ports.repositories.port_verification_evidence_repository import (
    PortVerificationEvidenceRepository,
)
from tiny_swarm_world.domain.inventory import VerificationResult
from tiny_swarm_world.infrastructure.adapters.repositories.local_state_paths import (
    local_state_file,
)


DEFAULT_VERIFICATION_EVIDENCE_PATH = Path("evidence") / "verification_results.json"


class VerificationEvidenceLocalRepository(PortVerificationEvidenceRepository):
    def __init__(
        self,
        root: Path | None = None,
        relative_path: str | Path = DEFAULT_VERIFICATION_EVIDENCE_PATH,
    ):
        self.path = local_state_file(root=root, relative_path=relative_path)

    def append(self, result: VerificationResult) -> None:
        results = [verification.to_dict() for verification in self.list_all()]
        results.append(result.to_dict())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"results": results}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def list_all(self) -> tuple[VerificationResult, ...]:
        if not self.path.exists():
            return ()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("verification evidence JSON root must be an object")
        results = data.get("results", ())
        if not isinstance(results, list):
            raise ValueError("verification evidence 'results' must be a list")
        return tuple(VerificationResult.from_dict(result) for result in _mapping_items(results))


def _mapping_items(results: list[object]) -> tuple[dict[str, Any], ...]:
    if not all(isinstance(result, dict) for result in results):
        raise ValueError("verification evidence results must be objects")
    return tuple(result for result in results if isinstance(result, dict))
