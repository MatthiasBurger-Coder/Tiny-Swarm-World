import re
from pathlib import Path

from tiny_swarm_world.application.ports.repositories.port_compose_file_repository import PortComposeFileRepository
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory
from tiny_swarm_world.infrastructure.project_paths import infra_root


STACK_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


class ComposeFileRepositoryYaml(PortComposeFileRepository):
    def __init__(self, base_directories: list[Path] | None = None):
        root = infra_root()
        self.base_directories = base_directories or [
            root / "config" / "compose",
            root / "compose",
        ]
        self.logger = LoggerFactory.get_logger(self.__class__)

    def get_compose_of(self, stack_name: str) -> StackDefinition:
        if not STACK_NAME_PATTERN.fullmatch(stack_name):
            raise ValueError("compose stack name contains invalid characters")

        for base_directory in self.base_directories:
            for compose_path in self._compose_paths_for(base_directory, stack_name):
                self.logger.info("Loaded compose file for stack '%s'.", stack_name)
                return StackDefinition(
                    name=stack_name,
                    compose_content=compose_path.read_text(encoding="utf-8"),
                )

        raise FileNotFoundError(f"No docker-compose.yml found for stack '{stack_name}' in {self.base_directories}.")

    def _compose_paths_for(self, base_directory: Path, stack_name: str) -> list[Path]:
        if not base_directory.is_dir():
            return []

        direct_path = base_directory / stack_name / "docker-compose.yml"
        if direct_path.is_file():
            return [direct_path]

        return sorted(
            compose_path
            for compose_path in base_directory.rglob("docker-compose.yml")
            if compose_path.parent.name == stack_name
        )
