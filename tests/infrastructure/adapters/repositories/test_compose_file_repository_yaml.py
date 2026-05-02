import tempfile
import unittest
from pathlib import Path

from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import ComposeFileRepositoryYaml


class TestComposeFileRepositoryYaml(unittest.TestCase):
    def test_loads_compose_content_from_matching_stack_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_root = Path(temp_dir) / "compose"
            config_root = Path(temp_dir) / "config" / "compose"
            config_root.joinpath("nexus").mkdir(parents=True)
            compose_file = config_root / "nexus" / "docker-compose.yml"
            compose_file.write_text("services:\n  nexus:\n    image: nexus:latest\n", encoding="utf-8")

            repository = ComposeFileRepositoryYaml(base_directories=[compose_root, config_root])
            stack_definition = repository.get_compose_of("nexus")

            self.assertEqual(stack_definition.name, "nexus")
            self.assertIn("image: nexus:latest", stack_definition.compose_content)

    def test_raises_when_stack_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_root = Path(temp_dir) / "compose"
            config_root = Path(temp_dir) / "config" / "compose"

            repository = ComposeFileRepositoryYaml(base_directories=[compose_root, config_root])

            with self.assertRaises(FileNotFoundError):
                repository.get_compose_of("missing-stack")
