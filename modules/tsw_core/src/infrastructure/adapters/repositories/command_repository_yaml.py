from pathlib import Path
from typing import Dict

from pydantic import ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from tiny_swarm_world.infrastructure.adapters.configuration.configuration_sources import validate_configuration_tree

from tiny_swarm_world.application.ports.repositories.port_command_repository import PortCommandRepository

from tiny_swarm_world.domain.command.command_entity import (
    CommandCatalogValidationError,
    CommandEntity,
)
from tiny_swarm_world.infrastructure.adapters.file_management.file_manager import FileManager
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory


class PortCommandRepositoryYaml(PortCommandRepository):
    """
    Loads and manages the task list from a YAML file using ruamel.yaml.
    """

    def __init__(self, filename: str, file_manager: FileManager | None = None):
        """
        :param filename: The name of the YAML file.
        """
        self.filename = filename
        self.logger = LoggerFactory.get_logger(self.__class__)
        self.file_manager = file_manager or FileManager()
        self.yaml = YAML(typ="safe")
        self.yaml.allow_duplicate_keys = False
        try:
            self.data = self.yaml.load(self.file_manager.load(path=Path(filename)))
            validate_configuration_tree(self.data)
        except (YAMLError, ValueError, OSError, UnicodeError, RecursionError):
            raise CommandCatalogValidationError("command catalog is not valid readable YAML") from None

    def get_all_commands(self) -> Dict[int, CommandEntity]:
        """
        Returns all commands from the YAML file.
        """
        if not isinstance(self.data, dict):
            raise CommandCatalogValidationError(
                f"{self.filename}: expected YAML root to be a dictionary"
            )

        unknown_root_fields = set(self.data) - {"commands"}
        if unknown_root_fields:
            raise CommandCatalogValidationError(
                f"{self.filename}: unsupported root fields"
            )

        commands = self.data.get("commands")
        if not isinstance(commands, list):
            raise CommandCatalogValidationError(
                f"{self.filename}: expected 'commands' to be a list"
            )

        task_dict: Dict[int, CommandEntity] = {}
        seen_ids: set[str] = set()
        for position, command in enumerate(commands, start=1):
            if not isinstance(command, dict):
                raise CommandCatalogValidationError(
                    f"{self.filename}: command entry {position} must be a dictionary"
                )

            try:
                _validate_scalar_types(command)
                command_entity = CommandEntity(**command)
            except (ValidationError, TypeError, ValueError):
                raise CommandCatalogValidationError(
                    f"command entry {position} failed validation"
                ) from None

            if command_entity.id in seen_ids:
                raise CommandCatalogValidationError(
                    f"command entry {position}: duplicate command id"
                )
            if command_entity.index in task_dict:
                raise CommandCatalogValidationError(
                    f"command entry {position}: duplicate command index"
                )

            seen_ids.add(command_entity.id)
            task_dict[command_entity.index] = command_entity

        return task_dict


def _validate_scalar_types(command: dict) -> None:
    index = command.get("index", 0)
    if isinstance(index, bool) or not isinstance(index, (int, str)):
        raise ValueError("command index must be an integer or numeric string")
    policy = command.get("evidence_policy")
    if policy is not None:
        if not isinstance(policy, dict):
            raise ValueError("command evidence policy must be a mapping")
        for field in ("redact_output", "store_raw_output"):
            if field in policy and not isinstance(policy[field], bool):
                raise ValueError("command evidence flags must be booleans")
