import tempfile
import unittest
from pathlib import Path

from ruamel.yaml import YAML

from tiny_swarm_world.domain.deployment import DEFAULT_SERVICE_STACK_CONTRACTS
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

    def test_default_search_order_prefers_config_compose_before_image_assets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            root.joinpath("compose", "jenkins").mkdir(parents=True)
            root.joinpath("config", "compose", "jenkins").mkdir(parents=True)
            root.joinpath("compose", "jenkins", "docker-compose.yml").write_text(
                "services:\n  jenkins:\n    image: image-asset-side\n",
                encoding="utf-8",
            )
            root.joinpath("config", "compose", "jenkins", "docker-compose.yml").write_text(
                "services:\n  jenkins:\n    image: config-side\n",
                encoding="utf-8",
            )

            repository = ComposeFileRepositoryYaml()
            repository.base_directories = [
                root / "config" / "compose",
                root / "compose",
            ]

            stack_definition = repository.get_compose_of("jenkins")

        self.assertIn("image: config-side", stack_definition.compose_content)
        self.assertNotIn("image: image-asset-side", stack_definition.compose_content)

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

    def test_committed_default_service_stack_compose_files_are_loadable(self):
        repository = ComposeFileRepositoryYaml()

        loaded_stack_names = [
            repository.get_compose_of(contract.stack_name).name
            for contract in DEFAULT_SERVICE_STACK_CONTRACTS
        ]

        self.assertEqual(
            ["portainer", "nexus", "jenkins", "rabbitmq", "sonarqube", "swagger"],
            loaded_stack_names,
        )

    def test_committed_default_service_stack_compose_files_declare_required_services(self):
        repository = ComposeFileRepositoryYaml()
        yaml = YAML(typ="safe")

        missing_services_by_stack: dict[str, list[str]] = {}
        for contract in DEFAULT_SERVICE_STACK_CONTRACTS:
            stack_definition = repository.get_compose_of(contract.stack_name)
            compose_data = yaml.load(stack_definition.compose_content)
            declared_services = set((compose_data.get("services") or {}).keys())
            missing_services = [
                service_name
                for service_name in contract.required_services
                if service_name not in declared_services
            ]
            if missing_services:
                missing_services_by_stack[contract.stack_name] = missing_services

        self.assertEqual({}, missing_services_by_stack)

    def test_committed_swagger_compose_uses_official_images_and_remote_openapi_bind(self):
        repository_root = Path(__file__).resolve().parents[4]
        compose_path = repository_root / "infra" / "config" / "compose" / "swagger" / "docker-compose.yml"
        compose_content = compose_path.read_text(encoding="utf-8")

        self.assertIn("image: docker.swagger.io/swaggerapi/swagger-editor", compose_content)
        self.assertIn("image: docker.swagger.io/swaggerapi/swagger-ui", compose_content)
        self.assertIn("image: nginx:mainline-alpine", compose_content)
        self.assertIn("SWAGGER_JSON: /openapi.json", compose_content)
        self.assertIn(
            "${TSW_REMOTE_STACK_ROOT:-/tmp/tiny-swarm-world/stacks}/swagger/swagger/openapi.json:/openapi.json:ro",
            compose_content,
        )
        self.assertIn(
            "${TSW_REMOTE_STACK_ROOT:-/tmp/tiny-swarm-world/stacks}/swagger/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro",
            compose_content,
        )
        self.assertNotIn("127.0.0.1:5000/swagger-nginx", compose_content)
        self.assertNotIn("depends_on", compose_content)
        self.assertNotIn("./swagger/openapi.json:/openapi.json", compose_content)
