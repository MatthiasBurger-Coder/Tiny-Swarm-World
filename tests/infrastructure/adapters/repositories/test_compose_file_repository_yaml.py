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

    def test_prefers_first_matching_base_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_root = Path(temp_dir) / "compose"
            config_root = Path(temp_dir) / "config" / "compose"
            compose_root.joinpath("portainer").mkdir(parents=True)
            config_root.joinpath("portainer").mkdir(parents=True)
            compose_root.joinpath("portainer", "docker-compose.yml").write_text(
                "services:\n  portainer:\n    image: preferred\n",
                encoding="utf-8",
            )
            config_root.joinpath("portainer", "docker-compose.yml").write_text(
                "services:\n  portainer:\n    image: fallback\n",
                encoding="utf-8",
            )

            repository = ComposeFileRepositoryYaml(base_directories=[compose_root, config_root])
            stack_definition = repository.get_compose_of("portainer")

            self.assertIn("image: preferred", stack_definition.compose_content)
            self.assertNotIn("image: fallback", stack_definition.compose_content)

    def test_raises_when_stack_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_root = Path(temp_dir) / "compose"
            config_root = Path(temp_dir) / "config" / "compose"

            repository = ComposeFileRepositoryYaml(base_directories=[compose_root, config_root])

            with self.assertRaises(FileNotFoundError):
                repository.get_compose_of("missing-stack")

    def test_rejects_stack_name_path_traversal(self):
        repository = ComposeFileRepositoryYaml(base_directories=[])

        with self.assertRaises(ValueError):
            repository.get_compose_of("../portainer")

    def test_rejects_invalid_stack_names(self):
        repository = ComposeFileRepositoryYaml(base_directories=[])

        for stack_name in ("", "../portainer", "/portainer", "Portainer", "portainer stack"):
            with self.subTest(stack_name=stack_name):
                with self.assertRaises(ValueError):
                    repository.get_compose_of(stack_name)

    def test_committed_portainer_compose_uses_docker_socket_mount(self):
        repository_root = Path(__file__).resolve().parents[4]
        compose_path = repository_root / "infra" / "config" / "compose" / "portainer" / "docker-compose.yml"
        compose_content = compose_path.read_text(encoding="utf-8")

        self.assertIn("/var/run/docker.sock:/var/run/docker.sock", compose_content)
        self.assertNotIn("/var/run/sock", compose_content)
