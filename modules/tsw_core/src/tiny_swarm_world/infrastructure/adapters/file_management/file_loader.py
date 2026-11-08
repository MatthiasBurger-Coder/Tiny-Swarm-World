from pathlib import Path
from typing import Any

from tiny_swarm_world.infrastructure.adapters.file_management.file_locator import FileLocator
from tiny_swarm_world.infrastructure.adapters.file_management.path_strategies.path_factory import PathFactory
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths


class FileLoader:
    """
    Handles loading of files in a generic way.
    """

    def __init__(
        self,
        filename: Path,
        path_factory: PathFactory | None = None,
        project_paths: ProjectPaths | None = None,
    ):
        """
        Initializes the file loader with the given filename.
        """
        self.path_factory = path_factory or PathFactory()
        self.file_locator = FileLocator(
            path_factory=self.path_factory,
            filename=filename.name,
            project_paths=project_paths,
        )
        self.filename = filename

    @property
    def path(self) -> Path:
        """Returns the absolute path to the file."""
        return Path(self.file_locator.get_existing_file_path())

    def load(self) -> Any:
        """Loads the file and returns its content."""
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                return file.read()

        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found: {self.path}") from e
        except Exception as e:
            raise RuntimeError(f"Error loading file {self.path}: {e}") from e
