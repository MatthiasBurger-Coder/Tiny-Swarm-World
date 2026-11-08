"""Read only the reviewed capability asset; no environment/version guessing."""
from pathlib import Path
import json

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ProfileCapabilityMatrix


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate capability field.')
        result[key] = value
    return result


class IncusProfileCapabilityRepository:
    def __init__(self, root: Path):
        self.path = root / 'modules/tsw_core/infra/config/incus-profile-capabilities.json'

    def load(self) -> ProfileCapabilityMatrix:
        try:
            if self.path.is_symlink() or not self.path.is_file() or self.path.stat().st_size > 65536:
                raise ValueError('Invalid capability asset.')
            raw = self.path.read_bytes()
            json.loads(raw, object_pairs_hook=_unique)
            return ProfileCapabilityMatrix.model_validate_json(raw)
        except (OSError, ValueError):
            raise LifecycleStateError('Scoped profile capability admission is unavailable; no mutation is allowed.') from None
