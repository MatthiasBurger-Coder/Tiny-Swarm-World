import tempfile
import tarfile
import unittest
from io import BytesIO
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from ruamel.yaml import YAML

from tiny_swarm_world.domain.artifacts import DEFAULT_CONTAINER_IMAGE_CONTRACTS
from tiny_swarm_world.domain.deployment import (
    DEFAULT_SERVICE_STACK_CONTRACTS,
    SERVICE_ACCESS_STACK_CONTRACT,
)
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc_swarm_runtime import (
    LxcContainerImagePublisher,
)
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

        self.assertEqual(["portainer", "nexus", "jenkins", "rabbitmq", "sonarqube", "swagger"], loaded_stack_names)

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

    def test_committed_jenkins_compose_uses_overridable_registry_image(self):
        repository_root = Path(__file__).resolve().parents[4]
        compose_path = (
            repository_root / "infra" / "config" / "compose" / "jenkins" / "docker-compose.yml"
        )
        compose_data = YAML(typ="safe").load(compose_path.read_text(encoding="utf-8"))

        self.assertEqual(
            "${TSW_JENKINS_IMAGE:-127.0.0.1:5000/jenkins:latest}",
            compose_data["services"]["jenkins"]["image"],
        )
        self.assertEqual(
            ["node.role == manager"],
            compose_data["services"]["jenkins"]["deploy"]["placement"]["constraints"],
        )
        self.assertEqual(
            ["jenkins_home:/var/lib/jenkins"],
            compose_data["services"]["jenkins"]["volumes"],
        )
        self.assertNotIn("secrets", compose_data)

    def test_committed_rabbitmq_compose_keeps_host_ports_on_manager_gateway(self):
        repository_root = Path(__file__).resolve().parents[4]
        compose_path = (
            repository_root / "infra" / "config" / "compose" / "rabbitmq" / "docker-compose.yml"
        )
        compose_data = YAML(typ="safe").load(compose_path.read_text(encoding="utf-8"))
        rabbitmq = compose_data["services"]["rabbitmq"]

        self.assertEqual(
            ["node.role == manager"],
            rabbitmq["deploy"]["placement"]["constraints"],
        )
        self.assertEqual(
            [
                {"target": 5672, "published": 5672, "protocol": "tcp", "mode": "host"},
                {"target": 15672, "published": 15672, "protocol": "tcp", "mode": "host"},
            ],
            rabbitmq["ports"],
        )

    def test_committed_swagger_compose_uses_official_images_and_remote_openapi_bind(self):
        repository_root = Path(__file__).resolve().parents[4]
        compose_path = repository_root / "infra" / "config" / "compose" / "swagger" / "docker-compose.yml"
        compose_content = compose_path.read_text(encoding="utf-8")
        yaml = YAML(typ="safe")
        compose_data = yaml.load(compose_content)

        self.assertIn("image: docker.swagger.io/swaggerapi/swagger-editor:v5.6.2-unprivileged", compose_content)
        self.assertIn("image: docker.swagger.io/swaggerapi/swagger-ui:v5.32.6", compose_content)
        self.assertIn("image: nginx:mainline-alpine", compose_content)
        self.assertEqual(
            [{"target": 80, "published": 8082, "protocol": "tcp", "mode": "host"}],
            compose_data["services"]["swagger-editor"]["ports"],
        )
        self.assertNotIn("ports", compose_data["services"]["swagger-api"])
        self.assertEqual(
            [{"target": 8084, "published": 8084, "protocol": "tcp", "mode": "host"}],
            compose_data["services"]["swagger-nginx"]["ports"],
        )
        self.assertIn("SWAGGER_JSON: /openapi.json", compose_content)
        self.assertIn(
            "${TSW_REMOTE_STACK_ROOT:-/var/lib/tiny-swarm-world/stacks}/swagger/swagger/openapi.json:/openapi.json:ro",
            compose_content,
        )
        self.assertIn(
            "${TSW_REMOTE_STACK_ROOT:-/var/lib/tiny-swarm-world/stacks}/swagger/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro",
            compose_content,
        )
        self.assertNotIn("127.0.0.1:5000/swagger-nginx", compose_content)
        self.assertNotIn("depends_on", compose_content)
        self.assertNotIn("./swagger/openapi.json:/openapi.json", compose_content)

    def test_committed_sonarqube_compose_waits_for_database_tcp_readiness(self):
        repository_root = Path(__file__).resolve().parents[4]
        compose_path = (
            repository_root / "infra" / "config" / "compose" / "sonarqube" / "docker-compose.yml"
        )
        compose_data = YAML(typ="safe").load(compose_path.read_text(encoding="utf-8"))
        command = compose_data["services"]["sonarqube"]["command"]

        self.assertEqual(("bash", "-lc"), tuple(command[:2]))
        self.assertEqual(
            "jdbc:postgresql://tasks.sonar_db:5432/sonar",
            compose_data["services"]["sonarqube"]["environment"]["SONAR_JDBC_URL"],
        )
        self.assertIn("/dev/tcp/tasks.sonar_db/5432", command[2])
        self.assertIn("/opt/sonarqube/docker/entrypoint.sh", command[2])

    def test_committed_service_access_compose_declares_required_services(self):
        repository_root = Path(__file__).resolve().parents[4]
        compose_path = repository_root / "infra" / "config" / "compose" / "service-access" / "docker-compose.yml"
        compose_content = compose_path.read_text(encoding="utf-8")
        compose_data = YAML(typ="safe").load(compose_content)
        services = compose_data["services"]

        self.assertEqual("service-access", ComposeFileRepositoryYaml().get_compose_of("service-access").name)
        self.assertEqual(set(SERVICE_ACCESS_STACK_CONTRACT.required_services), set(services))
        self.assertEqual(
            "${TSW_SERVICE_ACCESS_DASHBOARD_IMAGE:-127.0.0.1:5000/service-access-dashboard:latest}",
            services["service-access-dashboard"]["image"],
        )
        self.assertEqual(
            "${TSW_SERVICE_ACCESS_NGINX_IMAGE:-127.0.0.1:5000/service-access-nginx:latest}",
            services["service-access-nginx"]["image"],
        )
        self.assertEqual(
            [
                {"target": 80, "published": 80, "protocol": "tcp", "mode": "host"},
                {"target": 8086, "published": 8086, "protocol": "tcp", "mode": "host"},
                {"target": 443, "published": 443, "protocol": "tcp", "mode": "host"},
            ],
            services["service-access-nginx"]["ports"],
        )
        self.assertNotIn("secrets", compose_data)
        self.assertNotIn("volumes", compose_data)
        self.assertNotIn("${TSW_REMOTE_STACK_ROOT", compose_content)
        self.assertEqual(
            {"name": "service_access_link", "external": True},
            compose_data["networks"]["service_access_link"],
        )

    def test_committed_infisical_compose_declares_required_services_and_secret_boundary(self):
        repository_root = Path(__file__).resolve().parents[4]
        compose_path = repository_root / "infra" / "config" / "compose" / "infisical" / "docker-compose.yml"
        compose_content = compose_path.read_text(encoding="utf-8")
        compose_data = YAML(typ="safe").load(compose_content)
        services = compose_data["services"]

        self.assertEqual("infisical", ComposeFileRepositoryYaml().get_compose_of("infisical").name)
        self.assertEqual({"infisical", "infisical-db", "infisical-redis"}, set(services))
        self.assertEqual(
            "${TSW_INFISICAL_IMAGE:-infisical/infisical:latest}",
            services["infisical"]["image"],
        )
        self.assertEqual(
            "${TSW_INFISICAL_SITE_URL:-https://localhost}",
            services["infisical"]["environment"]["SITE_URL"],
        )
        self.assertEqual(
            "${TSW_INFISICAL_ENCRYPTION_KEY}",
            services["infisical"]["environment"]["ENCRYPTION_KEY"],
        )
        self.assertEqual(
            "${TSW_INFISICAL_AUTH_SECRET}",
            services["infisical"]["environment"]["AUTH_SECRET"],
        )
        self.assertEqual(
            "${TSW_INFISICAL_LOGIN_EMAIL}",
            services["infisical"]["environment"]["INITIAL_SUPER_ADMIN_EMAIL"],
        )
        self.assertEqual(
            "${TSW_INFISICAL_PASSWORD}",
            services["infisical"]["environment"]["INITIAL_SUPER_ADMIN_PASSWORD"],
        )
        self.assertEqual(
            "${TSW_INFISICAL_ADMIN_FIRST_NAME:-Admin}",
            services["infisical"]["environment"]["INITIAL_SUPER_ADMIN_FIRST_NAME"],
        )
        self.assertEqual(
            "${TSW_INFISICAL_ADMIN_LAST_NAME:-User}",
            services["infisical"]["environment"]["INITIAL_SUPER_ADMIN_LAST_NAME"],
        )
        self.assertNotIn("ports", services["infisical"])
        self.assertNotIn("secrets", compose_data)
        self.assertEqual(["infisical_pg_data:/var/lib/postgresql/data"], services["infisical-db"]["volumes"])
        self.assertEqual(["infisical_redis_data:/data"], services["infisical-redis"]["volumes"])
        self.assertEqual(
            {"name": "service_access_link", "external": True},
            compose_data["networks"]["service_access_link"],
        )

    def test_service_access_dashboard_and_nginx_are_image_packaged(self):
        repository_root = Path(__file__).resolve().parents[4]
        compose_data = YAML(typ="safe").load(
            (
                repository_root / "infra" / "config" / "compose" / "service-access" / "docker-compose.yml"
            ).read_text(encoding="utf-8")
        )
        packaged_services = {
            "service-access-dashboard": (
                repository_root / "infra" / "compose" / "service-access" / "dashboard" / "Dockerfile",
                "COPY index.html /usr/share/nginx/html/index.html",
            ),
            "service-access-nginx": (
                repository_root / "infra" / "compose" / "service-access" / "nginx" / "Dockerfile",
                "COPY default.conf /etc/nginx/conf.d/default.conf",
            ),
        }

        for service_name, (dockerfile_path, copy_line) in packaged_services.items():
            with self.subTest(service_name=service_name):
                service = compose_data["services"][service_name]
                self.assertIn("image", service)
                self.assertNotIn("build", service)
                self.assertNotIn("volumes", service)
                self.assertNotIn("configs", service)
                self.assertNotIn("secrets", service)
                self.assertTrue(dockerfile_path.is_file())
                dockerfile = dockerfile_path.read_text(encoding="utf-8")
                self.assertIn("FROM nginx:mainline-alpine", dockerfile)
                self.assertIn(copy_line, dockerfile)
                if service_name == "service-access-nginx":
                    self.assertIn("apk add --no-cache openssl", dockerfile)
                    self.assertIn("generate-self-signed-cert.sh", dockerfile)

    def test_service_access_image_publisher_packages_dashboard_and_nginx_assets(self):
        publisher = _CapturingImagePublisher()
        expected_archives = {
            "service-access-dashboard": {"Dockerfile", "index.html"},
            "service-access-nginx": {
                "Dockerfile",
                "default.conf",
                "generate-self-signed-cert.sh",
            },
        }

        for contract in DEFAULT_CONTAINER_IMAGE_CONTRACTS:
            if contract.build_context in expected_archives:
                with self.subTest(build_context=contract.build_context):
                    context_path = publisher._context_path(contract)
                    publisher._transfer_context(
                        context_path,
                        f"/remote/images/{contract.build_context}",
                    )
                    self.assertEqual(
                        expected_archives[contract.build_context],
                        publisher.archived_files[-1],
                    )

    def test_service_access_dashboard_exposes_management_table_columns(self):
        dashboard = _service_access_dashboard_html()

        for label in ("Server", "URL", "user", "pwd"):
            with self.subTest(label=label):
                self.assertIn(f">{label}<", dashboard)

    def test_service_access_dashboard_links_to_central_routes_without_credentials(self):
        dashboard = _service_access_dashboard_html()
        links = _extract_links(dashboard)

        self.assertTrue(links)
        self.assertEqual(
            {
                "/",
                "/jenkins",
                "/nexus",
                "/portainer",
                "/rabbitmq",
                "/sonarqube",
                "/swagger",
                "/infisical",
            },
            set(links),
        )
        for link in links:
            parsed = urlparse(link)
            self.assertFalse(parsed.username)
            self.assertFalse(parsed.password)
            self.assertEqual("", parsed.query)
            self.assertEqual("", parsed.fragment)
        for forbidden_link in (
            "http://localhost:8085",
            "http://localhost:9000",
            "http://localhost:8081",
            "http://localhost:8080",
            "http://localhost:15672",
            "http://localhost:9001",
        ):
            self.assertNotIn(forbidden_link, dashboard)

    def test_service_access_dashboard_lists_credential_references_without_values(self):
        dashboard = _service_access_dashboard_html()
        expected_items = (
            "platform/portainer",
            "platform/nexus",
            "platform/jenkins",
            "platform/rabbitmq",
            "platform/sonarqube",
        )

        for item in expected_items:
            with self.subTest(item=item):
                self.assertIn(f"<code>{item}</code>", dashboard)
        for forbidden in (
            "password=",
            "token=",
            "secret=",
            "api_key=",
            "access_token=",
            "Bearer ",
            "Basic ",
            "admin1234567890",
            "MyAdminPassWord1234-126354654",
            "adminPassword123",
        ):
            self.assertNotIn(forbidden, dashboard)


class _LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        attributes = dict(attrs)
        href = attributes.get("href")
        if href:
            self.links.append(href)


def _extract_links(html: str) -> list[str]:
    collector = _LinkCollector()
    collector.feed(html)
    return collector.links


class _CapturingImagePublisher(LxcContainerImagePublisher):
    def __init__(self):
        super().__init__(
            backend=ManagedLxcBackend.LXD,
            registry_username="registry-user",
            registry_password="registry-password",
        )
        self.archived_files: list[set[str]] = []

    def _run_manager_shell_bytes(
        self,
        script: str,
        *,
        input_bytes: bytes,
        timeout_seconds: int,
    ):
        with tarfile.open(fileobj=BytesIO(input_bytes), mode="r") as archive:
            self.archived_files.append(set(archive.getnames()))


def _service_access_dashboard_html() -> str:
    repository_root = Path(__file__).resolve().parents[4]
    return (
        repository_root / "infra" / "compose" / "service-access" / "dashboard" / "index.html"
    ).read_text(encoding="utf-8")
