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
    ServiceStackProfile,
    service_stack_contracts_for_profile,
)
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.domain.network import PortExposureClass, PortRegistry, ServicePortMapping
from tiny_swarm_world.domain.preflight import default_installation_plan
from tiny_swarm_world.infrastructure.adapters.clients.lxc_swarm_runtime import (
    LxcContainerImagePublisher,
)
from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import ComposeFileRepositoryYaml
from tiny_swarm_world.infrastructure.adapters.repositories.port_registry_yaml_repository import (
    PortRegistryYamlRepository,
)


class TestComposeFileRepositoryYaml(unittest.TestCase):
    def test_loads_compose_content_from_matching_stack_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_root = Path(temp_dir) / "compose"
            config_root = Path(temp_dir) / "config" / "compose"
            config_root.joinpath("nexus").mkdir(parents=True)
            compose_file = config_root / "nexus" / "docker-compose.yml"
            compose_file.write_text("services:\n  nexus:\n    image: nexus:latest\n    deploy: {}\n", encoding="utf-8")

            repository = ComposeFileRepositoryYaml(base_directories=[compose_root, config_root])
            stack_definition = repository.get_compose_of("nexus")

            self.assertEqual(stack_definition.name, "nexus")
            self.assertIn("image: nexus:latest", stack_definition.compose_content)

    def test_direct_published_port_rewrite_updates_changed_registry_port(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_root = Path(temp_dir) / "compose"
            stack_root = compose_root / "jenkins"
            stack_root.mkdir(parents=True)
            stack_root.joinpath("docker-compose.yml").write_text(
                "\n".join(
                    (
                        "services:",
                        "  jenkins:",
                        "    image: jenkins/jenkins:lts",
                        "    deploy: {}",
                        "    ports:",
                        "      - target: 8080",
                        "        published: 8080",
                        "        protocol: tcp",
                        "        mode: host",
                    )
                ),
                encoding="utf-8",
            )
            registry = PortRegistry(
                ranges=(),
                mappings=(
                    ServicePortMapping(
                        service_id="jenkins",
                        port_id="jenkins-http",
                        internal_port=8080,
                        external_port=18080,
                        exposure=PortExposureClass.DIRECT,
                    ),
                ),
            )
            repository = ComposeFileRepositoryYaml(
                base_directories=[compose_root],
                port_registry=registry,
            )

            stack_definition = repository.get_compose_of("jenkins")
            compose_data = YAML(typ="safe").load(stack_definition.compose_content)

        self.assertEqual(18080, compose_data["services"]["jenkins"]["ports"][0]["published"])

    def test_extracts_service_names_and_published_ports_from_compose_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_root = Path(temp_dir) / "compose"
            compose_root.joinpath("mixed").mkdir(parents=True)
            compose_root.joinpath("mixed", "docker-compose.yml").write_text(
                """
services:
  web:
    image: nginx
    deploy: {}
    ports:
      - target: 80
        published: 8080
        protocol: tcp
        mode: host
      - "127.0.0.1:8443:443/tcp"
      - "9000"
  worker:
    image: busybox
    deploy: {}
  admin:
    image: nginx
    deploy: {}
    ports:
      - published: "9090"
        target: 90
""",
                encoding="utf-8",
            )

            repository = ComposeFileRepositoryYaml(base_directories=[compose_root])

            services = repository.get_services_of("mixed")

        self.assertEqual(
            [
                ("web", (8080, 8443)),
                ("worker", ()),
                ("admin", (9090,)),
            ],
            [(service.name, service.published_ports) for service in services],
        )

    def test_recursively_loads_compose_content_from_matching_stack_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_root = Path(temp_dir) / "compose"
            config_root = Path(temp_dir) / "config" / "compose"
            config_root.joinpath("platform", "services", "nexus").mkdir(parents=True)
            compose_file = config_root / "platform" / "services" / "nexus" / "docker-compose.yml"
            compose_file.write_text("services:\n  nexus:\n    image: nested\n    deploy: {}\n", encoding="utf-8")

            repository = ComposeFileRepositoryYaml(base_directories=[compose_root, config_root])
            stack_definition = repository.get_compose_of("nexus")

            self.assertEqual(stack_definition.name, "nexus")
            self.assertIn("image: nested", stack_definition.compose_content)

    def test_prefers_first_matching_base_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_root = Path(temp_dir) / "compose"
            config_root = Path(temp_dir) / "config" / "compose"
            compose_root.joinpath("portainer").mkdir(parents=True)
            config_root.joinpath("portainer").mkdir(parents=True)
            compose_root.joinpath("portainer", "docker-compose.yml").write_text(
                "services:\n  portainer:\n    image: preferred\n    deploy: {}\n",
                encoding="utf-8",
            )
            config_root.joinpath("portainer", "docker-compose.yml").write_text(
                "services:\n  portainer:\n    image: fallback\n    deploy: {}\n",
                encoding="utf-8",
            )

            repository = ComposeFileRepositoryYaml(base_directories=[compose_root, config_root])
            stack_definition = repository.get_compose_of("portainer")

            self.assertIn("image: preferred", stack_definition.compose_content)
            self.assertNotIn("image: fallback", stack_definition.compose_content)

    def test_default_search_order_uses_config_compose(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            root.joinpath("config", "compose", "jenkins").mkdir(parents=True)
            root.joinpath("config", "compose", "jenkins", "docker-compose.yml").write_text(
                "services:\n  jenkins:\n    image: config-side\n    deploy: {}\n",
                encoding="utf-8",
            )

            repository = ComposeFileRepositoryYaml()
            repository.base_directories = [root / "config" / "compose"]

            stack_definition = repository.get_compose_of("jenkins")

        self.assertIn("image: config-side", stack_definition.compose_content)

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

    def test_rejects_compose_file_without_services_mapping(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_root = Path(temp_dir) / "compose"
            compose_root.joinpath("broken").mkdir(parents=True)
            compose_root.joinpath("broken", "docker-compose.yml").write_text(
                "name: broken\n",
                encoding="utf-8",
            )

            repository = ComposeFileRepositoryYaml(base_directories=[compose_root])

            with self.assertRaisesRegex(ValueError, "non-empty services mapping"):
                repository.get_compose_of("broken")

    def test_rejects_compose_service_without_deploy_mapping(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_root = Path(temp_dir) / "compose"
            compose_root.joinpath("broken").mkdir(parents=True)
            compose_root.joinpath("broken", "docker-compose.yml").write_text(
                "services:\n  web:\n    image: nginx\n",
                encoding="utf-8",
            )

            repository = ComposeFileRepositoryYaml(base_directories=[compose_root])

            with self.assertRaisesRegex(ValueError, "web"):
                repository.get_compose_of("broken")

    def test_rejects_compose_service_with_non_mapping_deploy_section(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            compose_root = Path(temp_dir) / "compose"
            compose_root.joinpath("broken").mkdir(parents=True)
            compose_root.joinpath("broken", "docker-compose.yml").write_text(
                "services:\n  web:\n    image: nginx\n    deploy: invalid\n",
                encoding="utf-8",
            )

            repository = ComposeFileRepositoryYaml(base_directories=[compose_root])

            with self.assertRaisesRegex(ValueError, "deploy mapping"):
                repository.get_compose_of("broken")

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
            ["portainer", "traefik", "nexus", "jenkins", "pulsar", "sonarqube", "swagger"],
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

    def test_committed_compose_metadata_exposes_service_names_and_published_ports(self):
        repository = ComposeFileRepositoryYaml()

        metadata = {
            stack: {
                service.name: service.published_ports
                for service in repository.get_services_of(stack)
            }
            for stack in (
                "jenkins",
                "infisical",
                "nexus",
                "portainer",
                "pulsar",
                "service-access",
                "sonarqube",
                "swagger",
                "traefik",
            )
        }

        self.assertEqual((11080, 11050), metadata["jenkins"]["jenkins"])
        self.assertEqual((17080,), metadata["infisical"]["infisical"])
        self.assertEqual((13081, 13500, 13501), metadata["nexus"]["nexus"])
        self.assertEqual((10000, 8086), metadata["service-access"]["service-access-nginx"])
        self.assertEqual((80, 443), metadata["traefik"]["traefik"])

    def test_committed_service_registry_aligns_selected_stacks_with_phase_and_ports(self):
        repository_root = Path(__file__).resolve().parents[4]
        registry = YAML(typ="safe").load(
            (repository_root / "infra" / "config" / "services.yml").read_text(
                encoding="utf-8"
            )
        )
        service_entries = registry["services"]
        expected_stacks = YAML(typ="safe").load(
            (
                repository_root / "infra" / "config" / "inventory" / "desired_inventory.yaml"
            ).read_text(encoding="utf-8")
        )["expected_stacks"]
        plan_phase_ids = {phase.phase_id for phase in default_installation_plan().phases}
        registry_port_ids = {mapping.port_id for mapping in PortRegistryYamlRepository().load().mappings}
        contract_by_stack = {
            contract.stack_name: contract
            for contract in service_stack_contracts_for_profile(ServiceStackProfile.SERVICE_ACCESS)
        }

        self.assertLessEqual(set(expected_stacks), set(service_entries))
        selected_stacks = expected_stacks
        self.assertEqual(set(), set(service_entries) - set(expected_stacks))
        self.assertEqual(set(selected_stacks), set(contract_by_stack))
        self.assertEqual(
            {
                "infisical",
                "jenkins",
                "nexus",
                "portainer",
                "pulsar",
                "service-access",
                "sonarqube",
                "swagger",
                "traefik",
            },
            set(service_entries),
        )

        for stack_name in selected_stacks:
            entry = service_entries[stack_name]
            with self.subTest(stack_name=stack_name):
                contract = contract_by_stack[stack_name]
                self.assertTrue(entry["enabled"])
                self.assertEqual(stack_name, entry["stack"])
                self.assertEqual(contract.phase_id, entry["phase"])
                self.assertIn(entry["phase"], plan_phase_ids)
                self.assertEqual(list(contract.required_services), entry["required_services"])
                self.assertEqual(list(contract.port_ids), entry["port_ids"])
                self.assertEqual(contract.service_readiness_target_id, entry["readiness_target"])
                self.assertLessEqual(set(entry["port_ids"]), registry_port_ids)

        self.assertEqual("network-routing", service_entries["traefik"]["phase"])
        self.assertEqual(["traefik"], service_entries["traefik"]["required_services"])
        self.assertLessEqual(set(service_entries["traefik"]["port_ids"]), registry_port_ids)

    def test_committed_compose_published_ports_are_registry_ingress_or_compatibility(self):
        repository = ComposeFileRepositoryYaml()
        repository_root = Path(__file__).resolve().parents[4]
        service_entries = YAML(typ="safe").load(
            (repository_root / "infra" / "config" / "services.yml").read_text(
                encoding="utf-8"
            )
        )["services"]
        registry_ports_by_id = {
            mapping.port_id: mapping.external_port
            for mapping in PortRegistryYamlRepository().load().mappings
        }

        for stack_name, entry in service_entries.items():
            published_ports = {
                port
                for service in repository.get_services_of(stack_name)
                for port in service.published_ports
            }
            registry_published_ports = {
                registry_ports_by_id[port_id]
                for port_id in entry["port_ids"]
                if registry_ports_by_id[port_id] is not None
            }
            classified_ports = (
                set(entry.get("compatibility_published_ports", ()))
                | set(entry.get("deferred_published_ports", ()))
                | set(entry.get("ingress_published_ports", ()))
                | registry_published_ports
            )

            with self.subTest(stack_name=stack_name):
                self.assertLessEqual(published_ports, classified_ports)

    def test_committed_health_checks_align_with_services_and_contracts(self):
        repository_root = Path(__file__).resolve().parents[4]
        health_checks = YAML(typ="safe").load(
            (repository_root / "infra" / "config" / "health-checks.yaml").read_text(
                encoding="utf-8"
            )
        )["checks"]
        service_entries = YAML(typ="safe").load(
            (repository_root / "infra" / "config" / "services.yml").read_text(
                encoding="utf-8"
            )
        )["services"]
        contract_by_stack = {
            contract.stack_name: contract
            for contract in service_stack_contracts_for_profile(ServiceStackProfile.SERVICE_ACCESS)
        }
        plan_phase_ids = {phase.phase_id for phase in default_installation_plan().phases}

        ids = [check["id"] for check in health_checks]
        target_ids = [check["target_id"] for check in health_checks]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(target_ids), len(set(target_ids)))

        checks_by_stack = {check["stack"]: check for check in health_checks}
        self.assertEqual(set(service_entries), set(checks_by_stack))
        for stack_name, entry in service_entries.items():
            check = checks_by_stack[stack_name]
            with self.subTest(stack_name=stack_name):
                self.assertFalse(check["live_default"])
                self.assertEqual("swarm_service_replicas", check["evidence_kind"])
                self.assertEqual(entry["readiness_target"], check["target_id"])
                self.assertEqual(entry["phase"], check["phase"])
                self.assertIn(check["phase"], plan_phase_ids)
                self.assertEqual(entry["required_services"], check["required_services"])
                if stack_name in contract_by_stack:
                    contract = contract_by_stack[stack_name]
                    self.assertEqual(contract.service_readiness_target_id, check["target_id"])
                    self.assertEqual(list(contract.required_services), check["required_services"])

    def test_committed_validation_plan_covers_required_health_check_targets(self):
        repository_root = Path(__file__).resolve().parents[4]
        health_checks = YAML(typ="safe").load(
            (repository_root / "infra" / "config" / "health-checks.yaml").read_text(
                encoding="utf-8"
            )
        )["checks"]
        validation_plan = YAML(typ="safe").load(
            (repository_root / "infra" / "config" / "validation-plan.yaml").read_text(
                encoding="utf-8"
            )
        )["plans"]["greenpath"]
        health_targets = {check["target_id"] for check in health_checks}
        required_targets = validation_plan["required_targets"]

        self.assertFalse(validation_plan["live_default"])
        self.assertEqual(len(required_targets), len(set(required_targets)))
        self.assertEqual(health_targets, set(required_targets))
        self.assertEqual([], validation_plan["optional_targets"])

    def test_committed_jenkins_compose_uses_overridable_registry_image(self):
        repository_root = Path(__file__).resolve().parents[4]
        compose_path = (
            repository_root / "infra" / "config" / "compose" / "jenkins" / "docker-compose.yml"
        )
        compose_data = YAML(typ="safe").load(compose_path.read_text(encoding="utf-8"))

        self.assertEqual(
            "${TSW_JENKINS_IMAGE:-127.0.0.1:13500/jenkins:0.2.0}",
            compose_data["services"]["jenkins"]["image"],
        )
        self.assertEqual(
            ["node.role == manager"],
            compose_data["services"]["jenkins"]["deploy"]["placement"]["constraints"],
        )
        self.assertEqual(
            [
                {"target": 8080, "published": 11080, "protocol": "tcp", "mode": "host"},
                {"target": 50000, "published": 11050, "protocol": "tcp", "mode": "host"},
            ],
            compose_data["services"]["jenkins"]["ports"],
        )
        self.assertEqual(
            ["jenkins_home:/var/lib/jenkins"],
            compose_data["services"]["jenkins"]["volumes"],
        )
        self.assertEqual(
            {"TSW_JENKINS_ADMIN_PASSWORD": "${TSW_JENKINS_ADMIN_PASSWORD}"},
            compose_data["services"]["jenkins"]["environment"],
        )
        self.assertNotIn("secrets", compose_data)
        self.assertNotEqual("root", compose_data["services"]["jenkins"].get("user"))

    def test_committed_nexus_compose_publishes_registry_ports_on_manager_host(self):
        repository_root = Path(__file__).resolve().parents[4]
        compose_path = (
            repository_root / "infra" / "config" / "compose" / "nexus" / "docker-compose.yml"
        )
        compose_data = YAML(typ="safe").load(compose_path.read_text(encoding="utf-8"))
        nexus = compose_data["services"]["nexus"]

        self.assertEqual(
            [
                {"target": 8081, "published": 13081, "protocol": "tcp", "mode": "host"},
                {"target": 5000, "published": 13500, "protocol": "tcp", "mode": "host"},
                {"target": 5001, "published": 13501, "protocol": "tcp", "mode": "host"},
            ],
            nexus["ports"],
        )
        self.assertEqual(
            ["node.role == manager"],
            nexus["deploy"]["placement"]["constraints"],
        )

    def test_committed_pulsar_compose_uses_standalone_with_non_conflicting_admin_port(self):
        repository_root = Path(__file__).resolve().parents[4]
        compose_path = (
            repository_root / "infra" / "config" / "compose" / "pulsar" / "docker-compose.yml"
        )
        compose_data = YAML(typ="safe").load(compose_path.read_text(encoding="utf-8"))
        pulsar = compose_data["services"]["pulsar"]

        self.assertEqual(
            "${TSW_PULSAR_IMAGE:-apachepulsar/pulsar:3.0.17}",
            pulsar["image"],
        )
        self.assertEqual(["sh", "-lc"], pulsar["command"][:2])
        self.assertIn("bin/apply-config-from-env.py conf/standalone.conf", pulsar["command"][-1])
        self.assertNotIn("bin/apply-config-from-env.py conf/bookkeeper.conf", pulsar["command"][-1])
        self.assertIn("exec bin/pulsar standalone", pulsar["command"][-1])
        self.assertIn("--advertised-address 127.0.0.1", pulsar["command"][-1])
        self.assertIn("--bookkeeper-port 3181", pulsar["command"][-1])
        self.assertIn("--no-functions-worker", pulsar["command"][-1])
        self.assertIn("--no-stream-storage", pulsar["command"][-1])
        self.assertEqual("true", pulsar["environment"]["PULSAR_PREFIX_authenticationEnabled"])
        self.assertEqual("127.0.0.1", pulsar["environment"]["PULSAR_PREFIX_advertisedAddress"])
        self.assertEqual(
            "org.apache.bookkeeper.bookie.InterleavedLedgerStorage",
            pulsar["environment"]["PULSAR_PREFIX_ledgerStorageClass"],
        )
        self.assertNotIn("PULSAR_PREFIX_zookeeperServers", pulsar["environment"])
        self.assertNotIn("PULSAR_PREFIX_zkServers", pulsar["environment"])
        self.assertNotIn("PULSAR_PREFIX_configurationStoreServers", pulsar["environment"])
        self.assertNotIn("PULSAR_PREFIX_metadataStoreUrl", pulsar["environment"])
        self.assertNotIn("PULSAR_PREFIX_configurationMetadataStoreUrl", pulsar["environment"])
        self.assertNotIn("PULSAR_PREFIX_metadataServiceUri", pulsar["environment"])
        self.assertNotIn("PULSAR_PREFIX_zooKeeperOperationTimeoutSeconds", pulsar["environment"])
        self.assertNotIn("PULSAR_PREFIX_zooKeeperSessionTimeoutMillis", pulsar["environment"])
        self.assertIn(
            "AuthenticationProviderToken",
            pulsar["environment"]["PULSAR_PREFIX_authenticationProviders"],
        )
        self.assertEqual(
            "data:;base64,${TSW_PULSAR_TOKEN_SECRET_KEY}",
            pulsar["environment"]["PULSAR_PREFIX_tokenSecretKey"],
        )
        self.assertNotIn("PULSAR_PREFIX_bookieId", pulsar["environment"])
        self.assertEqual(
            "-Xms512m -Xmx512m -XX:MaxDirectMemorySize=256m",
            pulsar["environment"]["PULSAR_MEM"],
        )
        self.assertEqual(
            "-XX:+UseG1GC -XX:+PerfDisableSharedMem",
            pulsar["environment"]["PULSAR_GC"],
        )
        self.assertEqual("", pulsar["environment"]["PULSAR_GC_LOG"])
        self.assertEqual(
            "-Djava.security.egd=file:/dev/./urandom -XX:TieredStopAtLevel=1 -XX:CICompilerCount=2",
            pulsar["environment"]["PULSAR_EXTRA_OPTS"],
        )
        self.assertEqual("${TSW_PULSAR_ADMIN_TOKEN}", pulsar["environment"]["TSW_PULSAR_ADMIN_TOKEN"])
        self.assertEqual(
            [
                {"target": 6650, "published": 14001, "protocol": "tcp", "mode": "host"},
                {"target": 8080, "published": 14080, "protocol": "tcp", "mode": "host"},
            ],
            pulsar["ports"],
        )
        self.assertNotIn(
            {"target": 8080, "published": 8080, "protocol": "tcp"},
            pulsar["ports"],
        )
        self.assertEqual(["pulsar-data:/pulsar/data"], pulsar["volumes"])
        self.assertIn("healthcheck", pulsar)
        self.assertIn("http://localhost:8080/admin/v2/clusters", pulsar["healthcheck"]["test"][-1])
        self.assertIn("TSW_PULSAR_ADMIN_TOKEN", pulsar["healthcheck"]["test"][-1])
        self.assertEqual(["service_access_link"], pulsar["networks"])
        self.assertEqual(
            {"name": "service_access_link", "external": True},
            compose_data["networks"]["service_access_link"],
        )
        self.assertEqual(
            ["node.role == manager"],
            pulsar["deploy"]["placement"]["constraints"],
        )

        pulsar_manager = compose_data["services"]["pulsar-manager"]
        self.assertEqual(
            "${TSW_PULSAR_MANAGER_IMAGE:-apachepulsar/pulsar-manager:v0.4.0}",
            pulsar_manager["image"],
        )
        self.assertEqual(
            "/pulsar-manager/pulsar-manager/application.properties",
            pulsar_manager["environment"]["SPRING_CONFIGURATION_FILE"],
        )
        self.assertEqual(
            [
                {"target": 9527, "published": 14081, "protocol": "tcp", "mode": "host"},
            ],
            pulsar_manager["ports"],
        )
        self.assertEqual(["7750"], pulsar_manager["expose"])
        self.assertEqual(["service_access_link"], pulsar_manager["networks"])
        self.assertEqual(
            ["node.role == manager"],
            pulsar_manager["deploy"]["placement"]["constraints"],
        )

        bootstrap = compose_data["services"]["pulsar-manager-bootstrap"]
        self.assertEqual(
            "${TSW_PULSAR_MANAGER_BOOTSTRAP_IMAGE:-python:3.12.13-alpine3.23}",
            bootstrap["image"],
        )
        self.assertEqual(
            "${TSW_PULSAR_MANAGER_ADMIN_PASSWORD}",
            bootstrap["environment"]["TSW_PULSAR_MANAGER_ADMIN_PASSWORD"],
        )
        self.assertIn("users/superuser", bootstrap["command"][-1])
        self.assertIn("admin@example.org", bootstrap["command"][-1])
        self.assertIn("pulsar-manager/login", bootstrap["command"][-1])
        self.assertIn('"username": "admin"', bootstrap["command"][-1])
        self.assertIn('"Host": backend_host_header', bootstrap["command"][-1])
        self.assertEqual(
            "http://tasks.pulsar-manager:7750",
            bootstrap["environment"]["TSW_PULSAR_MANAGER_BACKEND_URL"],
        )
        self.assertIn("backend_host_header = \"localhost:7750\"", bootstrap["command"][-1])
        self.assertIn("api_rejected_superuser", bootstrap["command"][-1])
        self.assertIn("exc.code != 400", bootstrap["command"][-1])
        self.assertIn('response.get("login") == "success"', bootstrap["command"][-1])
        self.assertIn("json.dumps", bootstrap["command"][-1])
        self.assertEqual("continue", bootstrap["deploy"]["update_config"]["failure_action"])
        self.assertEqual("none", bootstrap["deploy"]["restart_policy"]["condition"])

    def test_committed_swagger_compose_uses_official_images_and_remote_openapi_bind(self):
        repository_root = Path(__file__).resolve().parents[4]
        compose_path = repository_root / "infra" / "config" / "compose" / "swagger" / "docker-compose.yml"
        compose_content = compose_path.read_text(encoding="utf-8")
        yaml = YAML(typ="safe")
        compose_data = yaml.load(compose_content)

        self.assertIn("image: swaggerapi/swagger-editor:v5.6.2-unprivileged", compose_content)
        self.assertIn("image: swaggerapi/swagger-ui:v5.32.6", compose_content)
        self.assertIn("image: nginx:1.29.8-alpine", compose_content)
        self.assertNotIn("ports", compose_data["services"]["swagger-editor"])
        self.assertNotIn("ports", compose_data["services"]["swagger-api"])
        self.assertEqual(
            [{"target": 8084, "published": 16081, "protocol": "tcp", "mode": "host"}],
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
        entrypoint = compose_data["services"]["sonarqube"]["entrypoint"]
        command = compose_data["services"]["sonarqube"]["command"]

        self.assertEqual(("bash", "-lc"), tuple(entrypoint))
        self.assertEqual(
            "jdbc:postgresql://tasks.sonar_db:5432/sonar",
            compose_data["services"]["sonarqube"]["environment"]["SONAR_JDBC_URL"],
        )
        self.assertIn("/dev/tcp/tasks.sonar_db/5432", command[0])
        self.assertIn("/opt/sonarqube/docker/entrypoint.sh", command[0])
        self.assertIn("service_access_link", compose_data["services"]["sonarqube"]["networks"])
        self.assertIn("service_access_link", compose_data["services"]["sonar_db"]["networks"])
        self.assertEqual(
            [{"target": 9000, "published": 12000, "protocol": "tcp", "mode": "host"}],
            compose_data["services"]["sonarqube"]["ports"],
        )
        self.assertEqual(
            ["node.role == manager"],
            compose_data["services"]["sonarqube"]["deploy"]["placement"]["constraints"],
        )
        self.assertEqual(
            {"name": "service_access_link", "external": True},
            compose_data["networks"]["service_access_link"],
        )

    def test_committed_sonarqube_compose_uses_available_community_image(self):
        repository_root = Path(__file__).resolve().parents[4]
        compose_path = (
            repository_root / "infra" / "config" / "compose" / "sonarqube" / "docker-compose.yml"
        )
        compose_data = YAML(typ="safe").load(compose_path.read_text(encoding="utf-8"))

        self.assertEqual(
            "sonarqube:26.6.0.123539-community",
            compose_data["services"]["sonarqube"]["image"],
        )
        self.assertNotEqual(
            "sonarqube:lts-community",
            compose_data["services"]["sonarqube"]["image"],
        )

    def test_committed_service_access_compose_declares_required_services(self):
        repository_root = Path(__file__).resolve().parents[4]
        compose_path = repository_root / "infra" / "config" / "compose" / "service-access" / "docker-compose.yml"
        compose_content = compose_path.read_text(encoding="utf-8")
        compose_data = YAML(typ="safe").load(compose_content)
        services = compose_data["services"]

        self.assertEqual("service-access", ComposeFileRepositoryYaml().get_compose_of("service-access").name)
        self.assertEqual(set(SERVICE_ACCESS_STACK_CONTRACT.required_services), set(services))
        self.assertEqual(
            "${TSW_SERVICE_ACCESS_DASHBOARD_IMAGE:-127.0.0.1:13500/service-access-dashboard:0.2.0}",
            services["service-access-dashboard"]["image"],
        )
        self.assertEqual(
            "${TSW_SERVICE_ACCESS_NGINX_IMAGE:-127.0.0.1:13500/service-access-nginx:0.2.0}",
            services["service-access-nginx"]["image"],
        )
        self.assertEqual(
            [
                {"target": 80, "published": 10000, "protocol": "tcp", "mode": "host"},
                {"target": 8086, "published": 8086, "protocol": "tcp", "mode": "host"},
            ],
            services["service-access-nginx"]["ports"],
        )
        self.assertNotIn("secrets", compose_data)
        self.assertNotIn("volumes", compose_data)
        self.assertEqual(
            [
                {
                    "source": "service_access_dashboard_index",
                    "target": "/usr/share/nginx/html/index.html",
                }
            ],
            services["service-access-dashboard"]["configs"],
        )
        self.assertEqual(
            (
                "${TSW_REMOTE_STACK_ROOT:-/var/lib/tiny-swarm-world/stacks}"
                "/service-access/dashboard/index.html"
            ),
            compose_data["configs"]["service_access_dashboard_index"]["file"],
        )
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
            "${TSW_INFISICAL_IMAGE:-infisical/infisical:v0.159.1}",
            services["infisical"]["image"],
        )
        self.assertEqual(
            "${TSW_INFISICAL_SITE_URL:-http://localhost:17080}",
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
            services["infisical"]["environment"]["INITIAL_BOOTSTRAP_ADMIN_EMAIL"],
        )
        self.assertEqual(
            "${TSW_INFISICAL_BOOTSTRAP_ADMIN_PASSWORD}",
            services["infisical"]["environment"]["INITIAL_BOOTSTRAP_ADMIN_PASSWORD"],
        )
        self.assertEqual(
            "${TSW_INFISICAL_ADMIN_FIRST_NAME:-Tiny}",
            services["infisical"]["environment"]["INITIAL_BOOTSTRAP_ADMIN_FIRST_NAME"],
        )
        self.assertEqual(
            "${TSW_INFISICAL_ADMIN_LAST_NAME:-Admin}",
            services["infisical"]["environment"]["INITIAL_BOOTSTRAP_ADMIN_LAST_NAME"],
        )
        self.assertEqual(
            [{"target": 8080, "published": 17080, "protocol": "tcp", "mode": "host"}],
            services["infisical"]["ports"],
        )
        self.assertEqual(
            ["node.role == manager"],
            services["infisical"]["deploy"]["placement"]["constraints"],
        )
        self.assertNotIn("secrets", compose_data)
        self.assertEqual(["infisical_pg_data:/var/lib/postgresql/data"], services["infisical-db"]["volumes"])
        self.assertEqual(["infisical_redis_data:/data"], services["infisical-redis"]["volumes"])
        self.assertEqual(
            {"name": "service_access_link", "external": True},
            compose_data["networks"]["service_access_link"],
        )

    def test_committed_traefik_compose_defines_secure_swarm_ingress(self):
        repository_root = Path(__file__).resolve().parents[4]
        compose_path = repository_root / "infra" / "config" / "compose" / "traefik" / "docker-compose.yml"
        compose_content = compose_path.read_text(encoding="utf-8")
        compose_data = YAML(typ="safe").load(compose_content)
        traefik = compose_data["services"]["traefik"]
        command = traefik["command"]

        self.assertEqual("traefik", ComposeFileRepositoryYaml().get_compose_of("traefik").name)
        self.assertEqual("${TSW_TRAEFIK_IMAGE:-traefik:v3.7.4}", traefik["image"])
        self.assertIn("--entrypoints.web.address=:80", command)
        self.assertIn("--entrypoints.websecure.address=:443", command)
        self.assertIn("--entrypoints.web.http.redirections.entrypoint.to=websecure", command)
        self.assertIn("--providers.swarm=true", command)
        self.assertIn("--providers.swarm.exposedByDefault=false", command)
        self.assertIn("--providers.swarm.network=service_access_link", command)
        self.assertIn("--providers.file.filename=/etc/traefik/dynamic/tls.yml", command)
        self.assertNotIn("--api.insecure=true", compose_content)
        self.assertEqual(
            [
                {"target": 80, "published": 80, "protocol": "tcp", "mode": "host"},
                {"target": 443, "published": 443, "protocol": "tcp", "mode": "host"},
            ],
            traefik["ports"],
        )
        self.assertEqual(
            {"name": "service_access_link", "external": True},
            compose_data["networks"]["service_access_link"],
        )
        self.assertEqual(
            "${TSW_REMOTE_STACK_ROOT:-/var/lib/tiny-swarm-world/stacks}/traefik/dynamic/tls.yml",
            compose_data["configs"]["traefik_tls_dynamic_config"]["file"],
        )
        self.assertEqual(
            {"external": True},
            compose_data["secrets"]["tsw_traefik_tls_cert"],
        )
        self.assertEqual(
            {"external": True},
            compose_data["secrets"]["tsw_traefik_tls_key"],
        )
        self.assertEqual(
            "tsw_traefik_tls_cert",
            traefik["secrets"][0]["source"],
        )
        self.assertEqual(
            "tsw_traefik_tls_key",
            traefik["secrets"][1]["source"],
        )

    def test_committed_traefik_dynamic_tls_config_references_secret_mounts_only(self):
        repository_root = Path(__file__).resolve().parents[4]
        tls_path = repository_root / "infra" / "config" / "compose" / "traefik" / "dynamic" / "tls.yml"
        tls_content = tls_path.read_text(encoding="utf-8")
        tls_data = YAML(typ="safe").load(tls_content)

        certificate = tls_data["tls"]["certificates"][0]
        self.assertEqual("/run/secrets/tsw_traefik_tls_cert", certificate["certFile"])
        self.assertEqual("/run/secrets/tsw_traefik_tls_key", certificate["keyFile"])
        default_certificate = tls_data["tls"]["stores"]["default"]["defaultCertificate"]
        self.assertEqual("/run/secrets/tsw_traefik_tls_cert", default_certificate["certFile"])
        self.assertEqual("/run/secrets/tsw_traefik_tls_key", default_certificate["keyFile"])
        self.assertNotIn("BEGIN", tls_content)
        self.assertNotIn("PRIVATE KEY", tls_content)

    def test_committed_service_stacks_define_traefik_swarm_route_labels(self):
        expected = {
            "infisical": ("infisical", "infisical.tsw.local", "8080"),
            "jenkins": ("jenkins", "jenkins.tsw.local", "8080"),
            "nexus": ("nexus", "nexus.tsw.local", "8081"),
            "portainer": ("portainer", "portainer.tsw.local", "9000"),
            "service-access": ("service-access-dashboard", "service-access.tsw.local", "80"),
            "sonarqube": ("sonarqube", "sonarqube.tsw.local", "9000"),
            "swagger": ("swagger-nginx", "swagger.tsw.local", "8084"),
        }
        repository = ComposeFileRepositoryYaml()

        for stack_name, (service_name, hostname, upstream_port) in expected.items():
            with self.subTest(stack_name=stack_name):
                stack_definition = repository.get_compose_of(stack_name)
                compose_data = YAML(typ="safe").load(stack_definition.compose_content)
                service = compose_data["services"][service_name]
                labels = set(service["deploy"]["labels"])

                self.assertIn("service_access_link", service["networks"])
                self.assertEqual(
                    {"name": "service_access_link", "external": True},
                    compose_data["networks"]["service_access_link"],
                )
                self.assertIn("traefik.enable=true", labels)
                self.assertIn("traefik.swarm.network=service_access_link", labels)
                router_name = service_name.removesuffix("-dashboard").removesuffix("-nginx")
                self.assertIn(
                    f"traefik.http.routers.{router_name}.rule=Host(`{hostname}`)",
                    labels,
                )
                self.assertNotIn("Host(`localhost`)", repr(labels))
                self.assertIn(
                    f"traefik.http.routers.{router_name}.entrypoints=websecure",
                    labels,
                )
                self.assertIn(f"traefik.http.routers.{router_name}.tls=true", labels)
                self.assertIn(
                    (
                        f"traefik.http.services.{router_name}"
                        f".loadbalancer.server.port={upstream_port}"
                    ),
                    labels,
                )

    def test_rendered_pulsar_bootstrap_command_remains_valid_python(self):
        stack_definition = ComposeFileRepositoryYaml().get_compose_of("pulsar")
        compose_data = YAML(typ="safe").load(stack_definition.compose_content)
        script = compose_data["services"]["pulsar-manager-bootstrap"]["command"][2]

        self.assertIn("traefik.http.routers.pulsar.rule=Host(`pulsar.tsw.local`)", stack_definition.compose_content)
        self.assertTrue(script.startswith("python - <<'PY'\n"))
        python_source = script.removeprefix("python - <<'PY'\n").rsplit("\nPY", maxsplit=1)[0]
        compile(python_source, "pulsar-manager-bootstrap", "exec")
        self.assertNotIn("\n import urllib.error", script)
        self.assertNotIn("\n for _ in range(180):", script)

    def test_committed_service_stack_route_labels_are_renderer_owned(self):
        repository_root = Path(__file__).resolve().parents[4]
        compose_root = repository_root / "infra" / "config" / "compose"

        for compose_path in sorted(compose_root.glob("*/docker-compose.yml")):
            if compose_path.parent.name == "traefik":
                continue
            with self.subTest(compose_path=compose_path.as_posix()):
                raw_compose = compose_path.read_text(encoding="utf-8")

                self.assertNotIn("traefik.enable=", raw_compose)
                self.assertNotIn("traefik.swarm.network=", raw_compose)
                self.assertNotIn("traefik.http.routers.", raw_compose)
                self.assertNotIn("traefik.http.services.", raw_compose)

    def test_service_access_dashboard_and_nginx_are_image_packaged(self):
        repository_root = Path(__file__).resolve().parents[4]
        compose_data = YAML(typ="safe").load(
            (
                repository_root / "infra" / "config" / "compose" / "service-access" / "docker-compose.yml"
            ).read_text(encoding="utf-8")
        )
        packaged_services = {
            "service-access-dashboard": (
                repository_root
                / "infra"
                / "config"
                / "compose"
                / "service-access"
                / "dashboard"
                / "Dockerfile",
                "COPY --chown=nginx:nginx index.html /usr/share/nginx/html/index.html",
                "FROM nginx:1.29.8-alpine",
            ),
            "service-access-nginx": (
                repository_root
                / "infra"
                / "config"
                / "compose"
                / "service-access"
                / "nginx"
                / "Dockerfile",
                "COPY --chown=nginx:nginx default.conf /etc/nginx/conf.d/default.conf",
                "FROM nginx:1.29.8-alpine",
            ),
        }

        for service_name, (dockerfile_path, copy_line, base_image_line) in packaged_services.items():
            with self.subTest(service_name=service_name):
                service = compose_data["services"][service_name]
                self.assertIn("image", service)
                self.assertNotIn("build", service)
                self.assertNotIn("volumes", service)
                if service_name == "service-access-dashboard":
                    self.assertEqual(
                        [
                            {
                                "source": "service_access_dashboard_index",
                                "target": "/usr/share/nginx/html/index.html",
                            }
                        ],
                        service["configs"],
                    )
                    self.assertEqual(
                        (
                            "${TSW_REMOTE_STACK_ROOT:-/var/lib/tiny-swarm-world/stacks}"
                            "/service-access/dashboard/index.html"
                        ),
                        compose_data["configs"]["service_access_dashboard_index"]["file"],
                    )
                else:
                    self.assertNotIn("configs", service)
                self.assertNotIn("secrets", service)
                self.assertTrue(dockerfile_path.is_file())
                dockerfile = dockerfile_path.read_text(encoding="utf-8")
                self.assertIn(base_image_line, dockerfile)
                self.assertIn(copy_line, dockerfile)
                self.assertIn("pid /tmp/nginx.pid", dockerfile)
                self.assertNotIn("apk add", dockerfile)
                self.assertNotIn("setcap", dockerfile)
                if service_name == "service-access-nginx":
                    self.assertNotIn("generate-self-signed-cert.sh", dockerfile)

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

        for label in ("Service", "URL", "User", "Password"):
            with self.subTest(label=label):
                self.assertIn(f">{label}<", dashboard)

    def test_service_access_dashboard_is_rendered_from_effective_access_model(self):
        dashboard = _service_access_dashboard_html()
        rendered = ComposeFileRepositoryYaml().render_service_access_dashboard()

        self.assertEqual(rendered, dashboard)

    def test_service_access_dashboard_visible_text_is_english(self):
        dashboard = _service_access_dashboard_html()

        for expected in (
            "Management table for local Tiny Swarm World services and Infisical secret entries.",
            "Open Infisical",
            "Passwords are visible through Infisical",
            "Traefik routed access",
            "Open Infisical item",
            "Dashboard does not require a login",
            "Swagger/NGINX does not require a login",
            "This page does not store plaintext passwords.",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, dashboard)
        for forbidden in (
            "Verwaltungstabelle",
            "oeffnen",
            "Passwoerter",
            "Lokales",
            "anzeigen",
            "selbst",
            "keinen Login",
            "Passwortwerte",
            "Klartext",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, dashboard)

    def test_service_access_dashboard_links_to_allocated_ports_without_credentials(self):
        dashboard = _service_access_dashboard_html()
        links = _extract_links(dashboard)

        self.assertTrue(links)
        self.assertEqual(
            {
                "https://service-access.tsw.local",
                "https://portainer.tsw.local",
                "https://jenkins.tsw.local",
                "https://sonarqube.tsw.local",
                "https://nexus.tsw.local",
                "https://pulsar-api.tsw.local/admin/v2/clusters",
                "https://pulsar.tsw.local",
                "https://swagger.tsw.local",
                "https://infisical.tsw.local",
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
            "http://localhost:10000/jenkins",
            "http://localhost:10000/nexus",
            "http://localhost:10000/portainer",
            "http://localhost:10000/pulsar",
            "http://localhost:10000/pulsar-admin-api",
            "http://localhost:10000/sonarqube",
            "http://localhost:10000/swagger",
        ):
            self.assertNotIn(forbidden_link, dashboard)

    def test_service_access_dashboard_displays_allocated_service_ports(self):
        dashboard = _service_access_dashboard_html()

        for expected in (
            "https://service-access.tsw.local",
            "https://portainer.tsw.local",
            "https://jenkins.tsw.local",
            "https://sonarqube.tsw.local",
            "https://nexus.tsw.local",
            "https://pulsar-api.tsw.local/admin/v2/clusters",
            "https://pulsar.tsw.local",
            "https://swagger.tsw.local",
            "https://infisical.tsw.local",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, dashboard)
        for stale_url in (
            "http://localhost/jenkins",
            "http://localhost/nexus",
            "http://localhost/portainer",
            "http://localhost/pulsar",
            "http://localhost/pulsar-admin-api",
            "http://localhost/sonarqube",
            "http://localhost/swagger",
        ):
            with self.subTest(stale_url=stale_url):
                self.assertNotIn(stale_url, dashboard)

    def test_service_access_dashboard_links_open_new_tabs_safely(self):
        dashboard = _service_access_dashboard_html()
        collector = _LinkCollector()
        collector.feed(dashboard)

        self.assertTrue(collector.link_attributes)
        for attributes in collector.link_attributes:
            with self.subTest(href=attributes.get("href")):
                self.assertEqual("_blank", attributes.get("target"))
                rel_values = set((attributes.get("rel") or "").split())
                self.assertIn("noopener", rel_values)
                self.assertIn("noreferrer", rel_values)

    def test_service_access_dashboard_lists_credential_references_without_values(self):
        dashboard = _service_access_dashboard_html()
        expected_items = (
            "platform/portainer",
            "platform/nexus",
            "platform/jenkins",
            "platform/pulsar",
            "platform/pulsar-manager",
            "platform/sonarqube",
            "platform/infisical",
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
            "admin" + "Password123",
        ):
            self.assertNotIn(forbidden, dashboard)


class _LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []
        self.link_attributes: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        attributes = {key: value or "" for key, value in attrs}
        href = attributes.get("href")
        if href:
            self.links.append(href)
            self.link_attributes.append(attributes)


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
        repository_root
        / "infra"
        / "config"
        / "compose"
        / "service-access"
        / "dashboard"
        / "index.html"
    ).read_text(encoding="utf-8")
