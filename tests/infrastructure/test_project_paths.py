import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tiny_swarm_world.infrastructure import project_paths


class TestProjectPaths(unittest.TestCase):
    def test_repository_root_uses_environment_override(self):
        with TemporaryDirectory() as temporary_directory:
            configured_root = Path(temporary_directory) / "repository"
            configured_root.mkdir()

            with patch.dict(os.environ, {"TSW_REPOSITORY_ROOT": str(configured_root)}, clear=True):
                self.assertEqual(configured_root.resolve(), project_paths.repository_root())

    def test_infra_root_uses_environment_override(self):
        with TemporaryDirectory() as temporary_directory:
            configured_root = Path(temporary_directory) / "infra"
            configured_root.mkdir()

            with patch.dict(os.environ, {"TSW_INFRA_ROOT": str(configured_root)}, clear=True):
                self.assertEqual(configured_root.resolve(), project_paths.infra_root())

    def test_derived_roots_follow_repository_and_infra_roots(self):
        with TemporaryDirectory() as temporary_directory:
            repository_root = Path(temporary_directory) / "repository"
            infra_root = repository_root / "infra"
            infra_root.mkdir(parents=True)

            with patch.dict(
                os.environ,
                {
                    "TSW_REPOSITORY_ROOT": str(repository_root),
                    "TSW_INFRA_ROOT": str(infra_root),
                },
                clear=True,
            ):
                self.assertEqual(repository_root.resolve() / "src", project_paths.source_root())
                self.assertEqual(infra_root.resolve() / "config", project_paths.config_root())
                self.assertEqual(
                    repository_root.resolve() / ".tiny-swarm-world",
                    project_paths.local_state_root(),
                )
                self.assertEqual(
                    repository_root.resolve() / ".tiny-swarm-world" / "logs",
                    project_paths.logs_root(),
                )


if __name__ == "__main__":
    unittest.main()
