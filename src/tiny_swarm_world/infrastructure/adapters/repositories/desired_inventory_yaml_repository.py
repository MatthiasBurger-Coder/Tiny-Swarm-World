from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from tiny_swarm_world.application.ports.repositories.port_desired_inventory_repository import (
    PortDesiredInventoryRepository,
)
from tiny_swarm_world.domain.inventory import DesiredInventory
from tiny_swarm_world.infrastructure.project_paths import config_root


DEFAULT_DESIRED_INVENTORY_PATH = Path("inventory") / "desired_inventory.yaml"


class DesiredInventoryYamlRepository(PortDesiredInventoryRepository):
    def __init__(self, path: Path | None = None):
        self.path = path or (config_root() / DEFAULT_DESIRED_INVENTORY_PATH)
        self.yaml = YAML(typ="safe")

    def load(self) -> DesiredInventory:
        if not self.path.exists():
            return DesiredInventory()

        data = self.yaml.load(self.path.read_text(encoding="utf-8"))
        if data is None:
            return DesiredInventory()
        if not isinstance(data, dict):
            raise ValueError("desired inventory YAML root must be a mapping")
        return DesiredInventory.from_dict(data)
