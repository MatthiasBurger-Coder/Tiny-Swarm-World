from pathlib import Path

from tiny_swarm_world.infrastructure.adapters.file_management.file_locator import FileLocator
from tiny_swarm_world.infrastructure.adapters.file_management.path_strategies.path_factory import PathFactory
from tiny_swarm_world.infrastructure.dependency_injection.infra_core_di_annotations import inject
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory


class FileSaver:
    """
    Handles saving files in a generic way.
    """

    @inject
    def __init__(self, filename: Path, path_factory: PathFactory):
        """
        Initializes the file saver with the given file path.
        """
        self.logger = LoggerFactory.get_logger(self.__class__)
        self.file_locator = FileLocator(path_factory=path_factory, filename=filename.name)
        self.filename = filename

    @property
    def path(self) -> Path:
        """Returns the absolute path to the file."""
        return Path(self.file_locator.get_existing_file_path())

    def save(self, content: str):
        """Saves the given content to the file."""
        try:
            self.logger.info(f"save to: {self.path}")
            with open(self.path, "w", encoding="utf-8") as file:
                file.write(content)

        except Exception as e:
            self.logger.error(f"Error saving file {self.path}: {e}")
            raise RuntimeError(f"Error saving file {self.path}: {e}") from e
