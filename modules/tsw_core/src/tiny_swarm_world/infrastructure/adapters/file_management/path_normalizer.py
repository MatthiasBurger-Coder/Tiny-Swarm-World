from pathlib import Path
from typing import Any

from tiny_swarm_world.infrastructure.adapters.file_management.path_strategies.path_factory import PathFactory


class PathNormalizer:
    """
    Handles path normalization and directory management using a factory-based approach.
    """

    def __init__(self, input_path: Any, path_factory: Any = None):
        if hasattr(input_path, "get_strategy") and path_factory is not None:
            input_path, path_factory = path_factory, input_path
        if path_factory is None:
            path_factory = PathFactory()
        self.strategy = path_factory.get_strategy()
        self.raw_path = Path(input_path) if isinstance(input_path, str) else input_path

    def normalize(self) -> str:
        """
        Normalizes the given path using the OS-specific strategy.

        Returns:
            str: A normalized absolute file path.
        """
        return self.strategy.normalize(self.raw_path)

    def ensure_directory(self) -> str:
        """
        Ensures that the directory exists and creates it if necessary.

        Returns:
            str: The absolute path to the directory.
        """
        dir_path = self.normalize()

        if not Path(dir_path).exists():
            Path(dir_path).mkdir(parents=True, exist_ok=True)

        return dir_path

    def basename(self) -> str:
        """
        Returns the filename without the full path.

        Returns:
            str: The base name of the file.
        """
        return self.raw_path.name

    def parent_directory(self) -> str:
        """
        Returns the parent directory of the given path.
        Ensures the result is absolute if the input was relative.

        Returns:
            str: The parent directory path.
        """
        return Path(self.raw_path).resolve().parent.as_posix()
