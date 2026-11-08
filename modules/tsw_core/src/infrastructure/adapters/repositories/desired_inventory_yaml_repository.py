from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from tiny_swarm_world.infrastructure.adapters.configuration.configuration_sources import validate_configuration_tree

from tiny_swarm_world.application.ports.repositories.port_desired_inventory_repository import (
    PortDesiredInventoryRepository,
)
from tiny_swarm_world.domain.inventory import DesiredInventory
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths, default_project_paths


DEFAULT_DESIRED_INVENTORY_PATH = Path("inventory") / "desired_inventory.yaml"


class DesiredInventoryYamlRepository(PortDesiredInventoryRepository):
    def __init__(self, path: Path | None = None, project_paths: ProjectPaths | None = None):
        paths = project_paths or default_project_paths()
        self.path = path or (paths.config_root / DEFAULT_DESIRED_INVENTORY_PATH)
        self.yaml = YAML(typ="safe")
        self.yaml.allow_duplicate_keys = False

    def load(self) -> DesiredInventory:
        if not self.path.exists():
            return DesiredInventory()

        try:
            data = self.yaml.load(self.path.read_text(encoding="utf-8"))
        except (YAMLError, OSError, UnicodeError, RecursionError):
            raise ValueError("desired inventory could not be read as valid YAML") from None
        validate_configuration_tree(data)
        if data is None:
            return DesiredInventory()
        if not isinstance(data, dict):
            raise ValueError("desired inventory YAML root must be a mapping")
        return DesiredInventory.from_dict(data)
