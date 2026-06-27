from pathlib import Path
from typing import Any

from tiny_swarm_world.application.ports.file_management.port_file_manager import PortFileManager
from tiny_swarm_world.infrastructure.adapters.file_management.file_creator import FileCreator
from tiny_swarm_world.infrastructure.adapters.file_management.file_loader import FileLoader
from tiny_swarm_world.infrastructure.adapters.file_management.file_locator import FileLocator
from tiny_swarm_world.infrastructure.adapters.file_management.file_saver import FileSaver
from tiny_swarm_world.infrastructure.adapters.file_management.path_normalizer import PathNormalizer
from tiny_swarm_world.infrastructure.adapters.file_management.path_strategies.path_factory import PathFactory
from tiny_swarm_world.infrastructure.dependency_injection.infra_core_di_annotations import inject
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths, default_project_paths


class FileManager(PortFileManager):
    """
    Concrete implementation of the FileManager that manages file loading, saving, creating, and deleting.
    """

    @inject
    def __init__(
        self,
        path_factory: PathFactory,
        project_paths: ProjectPaths | None = None,
    ):
        """
        Initializes the FileManager with locator, loader, saver, and creator instances.
        """
        self.logger = LoggerFactory.get_logger(self.__class__)
        self.path_factory = path_factory
        paths = project_paths or default_project_paths()
        # Use lambdas to defer instantiation with required dependencies
        self.locator = lambda filename: FileLocator(
            PathNormalizer(paths.config_root).normalize()
        )
        self.loader = FileLoader
        self.saver = FileSaver
        self.creator = FileCreator

    def load(self, path: Path) -> Any:
        """
        Loads the file content using the loader.

        Args:
            path (Path): The file path.

        Returns:
            Any: The loaded data.
        """
        file_loader = self.loader(path)
        return file_loader.load()

    def save(self, path: Path, data: Any) -> None:
        """
        Saves data to the specified file using the saver.

        Args:
            path (Path): The file path.
            data (Any): The data to be saved.
        """
        self.logger.info(f"Save to {path} with : {data}")
        file_saver = self.saver(path)
        file_saver.save(data)

    def create(self, path: Path, data: Any) -> None:
        """
        Creates a new file using the creator.

        Args:
            path (Path): The file path where the file should be created.
            data (Any): The data to be stored.
        """
        self.creator().create(path, data)

    def delete(self, path: Path) -> bool:
        """
        Deletes a file.

        Args:
            path (Path): The file path.

        Returns:
            bool: True if the file was deleted, False otherwise.
        """
        try:
            file_path = Path(path)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            raise RuntimeError(f"Error deleting file {path}: {e}") from e
