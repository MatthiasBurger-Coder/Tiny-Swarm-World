from pathlib import Path

from application.ports.repositories.port_compose_file_repository import PortComposeFileRepository
from domain.deployment.stack_definition import StackDefinition
from infrastructure.logging.logger_factory import LoggerFactory


class ComposeFileRepositoryYaml(PortComposeFileRepository):
    def __init__(self, base_directories: list[Path] | None = None):
        docker_root = Path(__file__).resolve().parents[3]
        self.base_directories = base_directories or [
            docker_root / "compose",
            docker_root / "config" / "compose",
        ]
        self.logger = LoggerFactory.get_logger(self.__class__)

    def get_compose_of(self, stack_name: str) -> StackDefinition:
        for base_directory in self.base_directories:
            compose_path = base_directory / stack_name / "docker-compose.yml"
            if compose_path.is_file():
                self.logger.info(f"Loaded compose file for stack '{stack_name}' from {compose_path}.")
                return StackDefinition(
                    name=stack_name,
                    compose_content=compose_path.read_text(encoding="utf-8"),
                )

        raise FileNotFoundError(f"No docker-compose.yml found for stack '{stack_name}' in {self.base_directories}.")
