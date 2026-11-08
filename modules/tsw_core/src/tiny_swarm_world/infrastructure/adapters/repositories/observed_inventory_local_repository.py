from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tiny_swarm_world.application.ports.repositories.port_observed_inventory_repository import (
    PortObservedInventoryRepository,
)
from tiny_swarm_world.domain.inventory import ObservedInventory
from tiny_swarm_world.infrastructure.adapters.repositories.local_state_paths import (
    local_state_file,
)


DEFAULT_OBSERVED_INVENTORY_PATH = Path("inventory") / "observed_inventory.json"


class ObservedInventoryLocalRepository(PortObservedInventoryRepository):
    def __init__(
        self,
        root: Path | None = None,
        relative_path: str | Path = DEFAULT_OBSERVED_INVENTORY_PATH,
    ):
        self.path = local_state_file(root=root, relative_path=relative_path)

    def load(self) -> ObservedInventory:
        if not self.path.exists():
            return ObservedInventory()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("observed inventory JSON root must be an object")
        return ObservedInventory.from_dict(data)

    def save(self, inventory: ObservedInventory) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(_inventory_payload(inventory), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _inventory_payload(inventory: ObservedInventory) -> dict[str, Any]:
    return inventory.to_dict()
