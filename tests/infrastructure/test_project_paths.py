import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tiny_swarm_world.infrastructure import project_paths
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths


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

    def test_project_paths_from_roots_derives_all_paths(self):
        with TemporaryDirectory() as temporary_directory:
            repository_root = Path(temporary_directory) / "repository"
            infra_root = Path(temporary_directory) / "infra-override"
            repository_root.mkdir()
            infra_root.mkdir()

            paths = ProjectPaths.from_roots(repository_root, infra_root)

            self.assertEqual(repository_root.resolve(), paths.repository_root)
            self.assertEqual(repository_root.resolve() / "src", paths.source_root)
            self.assertEqual(infra_root.resolve(), paths.infra_root)
            self.assertEqual(infra_root.resolve() / "config", paths.config_root)
            self.assertEqual(
                repository_root.resolve() / ".tiny-swarm-world",
                paths.local_state_root,
            )
            self.assertEqual(
                repository_root.resolve() / ".tiny-swarm-world" / "logs",
                paths.logs_root,
            )

    def test_project_paths_from_environment_preserves_overrides(self):
        with TemporaryDirectory() as temporary_directory:
            repository_root = Path(temporary_directory) / "repository"
            infra_root = Path(temporary_directory) / "infra"
            repository_root.mkdir()
            infra_root.mkdir()

            with patch.dict(
                os.environ,
                {
                    "TSW_REPOSITORY_ROOT": str(repository_root),
                    "TSW_INFRA_ROOT": str(infra_root),
                },
                clear=True,
            ):
                paths = ProjectPaths.from_environment()

            self.assertEqual(repository_root.resolve(), paths.repository_root)
            self.assertEqual(infra_root.resolve(), paths.infra_root)

    def test_default_project_paths_feeds_compatibility_functions(self):
        with TemporaryDirectory() as temporary_directory:
            repository_root = Path(temporary_directory) / "repository"
            infra_root = Path(temporary_directory) / "infra"
            repository_root.mkdir()
            infra_root.mkdir()

            with patch.dict(
                os.environ,
                {
                    "TSW_REPOSITORY_ROOT": str(repository_root),
                    "TSW_INFRA_ROOT": str(infra_root),
                },
                clear=True,
            ):
                paths = project_paths.default_project_paths()
                self.assertEqual(paths.repository_root, project_paths.repository_root())
                self.assertEqual(paths.source_root, project_paths.source_root())
                self.assertEqual(paths.infra_root, project_paths.infra_root())
                self.assertEqual(paths.config_root, project_paths.config_root())
                self.assertEqual(paths.local_state_root, project_paths.local_state_root())
                self.assertEqual(paths.logs_root, project_paths.logs_root())


if __name__ == "__main__":
    unittest.main()
