from pathlib import Path

from tiny_swarm_world.infrastructure.adapters.file_management.path_strategies.path_strategy import PathStrategy

class PathLinuxStrategy(PathStrategy):
    def normalize(self, path: Path) -> str:
        """Returns an absolute path for Linux without modification."""
        return path.resolve().as_posix()