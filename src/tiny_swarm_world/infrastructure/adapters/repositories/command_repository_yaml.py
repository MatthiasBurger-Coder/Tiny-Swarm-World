from pathlib import Path
from typing import Dict

from pydantic import ValidationError
from ruamel.yaml import YAML

from tiny_swarm_world.application.ports.repositories.port_command_repository import PortCommandRepository

from tiny_swarm_world.domain.command.command_entity import (
    CommandCatalogValidationError,
    CommandEntity,
)
from tiny_swarm_world.infrastructure.adapters.file_management.file_manager import FileManager
from tiny_swarm_world.infrastructure.dependency_injection.infra_core_di_container import infra_core_container
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
        self.file_manager = file_manager or infra_core_container.resolve(FileManager)
        self.yaml = YAML()
        self.data = self.yaml.load(self.file_manager.load(path=Path(filename))) or {}

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
                f"{self.filename}: unsupported root fields: {sorted(unknown_root_fields)}"
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
                command_entity = CommandEntity(**command)
            except (ValidationError, TypeError) as exc:
                raise CommandCatalogValidationError(
                    f"{self.filename}: command entry {position} failed validation: {exc}"
                ) from exc

            if command_entity.id in seen_ids:
                raise CommandCatalogValidationError(
                    f"{self.filename}: duplicate command id '{command_entity.id}'"
                )
            if command_entity.index in task_dict:
                raise CommandCatalogValidationError(
                    f"{self.filename}: duplicate command index '{command_entity.index}'"
                )

            seen_ids.add(command_entity.id)
            task_dict[command_entity.index] = command_entity

        return task_dict
