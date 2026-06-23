import re
from collections.abc import Mapping
from io import StringIO
from pathlib import Path

from ruamel.yaml import YAML

from tiny_swarm_world.application.ports.repositories.port_compose_file_repository import PortComposeFileRepository
from tiny_swarm_world.domain.deployment.stack_definition import (
    ComposeServiceDefinition,
    StackDefinition,
)
from tiny_swarm_world.domain.network import PortRegistry
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory
from tiny_swarm_world.infrastructure.project_paths import infra_root
from tiny_swarm_world.infrastructure.adapters.repositories.port_registry_yaml_repository import (
    PortRegistryYamlRepository,
)


STACK_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
_YAML = YAML(typ="safe")


class ComposeFileRepositoryYaml(PortComposeFileRepository):
    def __init__(
        self,
        base_directories: list[Path] | None = None,
        port_registry: PortRegistry | None = None,
    ):
        root = infra_root()
        self.base_directories = base_directories or [
            root / "config" / "compose",
        ]
        self.port_registry = port_registry or PortRegistryYamlRepository().load()
        self.logger = LoggerFactory.get_logger(self.__class__)

    def get_compose_of(self, stack_name: str) -> StackDefinition:
        if not STACK_NAME_PATTERN.fullmatch(stack_name):
            raise ValueError("compose stack name contains invalid characters")

        for base_directory in self.base_directories:
            for compose_path in self._compose_paths_for(base_directory, stack_name):
                compose_content = compose_path.read_text(encoding="utf-8")
                _validate_swarm_stack_compose(stack_name, compose_content)
                compose_content = _resolve_direct_published_ports(
                    stack_name,
                    compose_content,
                    self.port_registry,
                )
                self.logger.info("Loaded compose file for stack '%s'.", stack_name)
                return StackDefinition(
                    name=stack_name,
                    compose_content=compose_content,
                )

        raise FileNotFoundError(f"No docker-compose.yml found for stack '{stack_name}' in {self.base_directories}.")

    def get_services_of(self, stack_name: str) -> tuple[ComposeServiceDefinition, ...]:
        stack_definition = self.get_compose_of(stack_name)
        payload = _YAML.load(stack_definition.compose_content) or {}
        if not isinstance(payload, Mapping):
            return ()
        services = payload.get("services", {})
        if not isinstance(services, Mapping):
            return ()

        return tuple(
            ComposeServiceDefinition(
                name=service_name,
                published_ports=_published_ports_from_service(service_payload),
            )
            for service_name, service_payload in services.items()
            if isinstance(service_name, str) and isinstance(service_payload, Mapping)
        )

    def _compose_paths_for(self, base_directory: Path, stack_name: str) -> list[Path]:
        if not base_directory.is_dir():
            return []

        direct_path = base_directory / stack_name / "docker-compose.yml"
        if direct_path.is_file():
            return [direct_path]

        return sorted(
            compose_path
            for compose_path in base_directory.rglob("docker-compose.yml")
            if compose_path.parent.name == stack_name
        )


def _published_ports_from_service(service_payload: Mapping[object, object]) -> tuple[int, ...]:
    ports = service_payload.get("ports", ())
    if not isinstance(ports, list):
        return ()

    published_ports: list[int] = []
    for port in ports:
        published = _published_port_from_entry(port)
        if published is not None:
            published_ports.append(published)
    return tuple(dict.fromkeys(published_ports))


def _validate_swarm_stack_compose(stack_name: str, compose_content: str) -> None:
    payload = _YAML.load(compose_content) or {}
    if not isinstance(payload, Mapping):
        raise ValueError(f"compose stack '{stack_name}' must be a YAML mapping")

    services = payload.get("services")
    if not isinstance(services, Mapping) or not services:
        raise ValueError(f"compose stack '{stack_name}' must define a non-empty services mapping")

    invalid_services: list[str] = []
    for service_name, service_payload in services.items():
        if not isinstance(service_name, str):
            invalid_services.append(str(service_name))
            continue
        if not isinstance(service_payload, Mapping):
            invalid_services.append(service_name)
            continue
        deploy = service_payload.get("deploy")
        if not isinstance(deploy, Mapping):
            invalid_services.append(service_name)

    if invalid_services:
        invalid = ", ".join(sorted(invalid_services))
        raise ValueError(f"compose stack '{stack_name}' has services without a deploy mapping: {invalid}")


def _published_port_from_entry(port_entry: object) -> int | None:
    if isinstance(port_entry, Mapping):
        return _published_port_from_value(port_entry.get("published"))
    if isinstance(port_entry, str):
        return _published_port_from_short_syntax(port_entry)
    return None


def _published_port_from_value(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _published_port_from_short_syntax(value: str) -> int | None:
    port_without_protocol = value.rsplit("/", 1)[0]
    if ":" not in port_without_protocol:
        return None
    host_side = port_without_protocol.rsplit(":", 1)[0]
    if host_side.startswith("[") and "]:" in host_side:
        host_side = host_side.rsplit("]:", 1)[1]
    elif ":" in host_side:
        host_side = host_side.rsplit(":", 1)[1]
    if "-" in host_side:
        host_side = host_side.split("-", 1)[0]
    return int(host_side) if host_side.isdigit() else None


def _resolve_direct_published_ports(
    stack_name: str,
    compose_content: str,
    port_registry: PortRegistry,
) -> str:
    payload = _YAML.load(compose_content) or {}
    if not isinstance(payload, Mapping):
        return compose_content
    services = payload.get("services")
    if not isinstance(services, Mapping):
        return compose_content

    mutated = False
    ports_by_id = {mapping.port_id: mapping for mapping in port_registry.mappings}
    for service_name, service_payload in services.items():
        if not isinstance(service_name, str) or not isinstance(service_payload, Mapping):
            continue
        configured_ports = service_payload.get("ports")
        if not isinstance(configured_ports, list):
            continue

        for entry in configured_ports:
            if not isinstance(entry, dict):
                continue
            port_id = _port_id_for_entry(stack_name, service_name, entry)
            if port_id is None:
                continue
            mapping = ports_by_id.get(port_id)
            if mapping is None or mapping.external_port is None:
                continue
            if entry.get("published") == mapping.external_port:
                continue
            entry["published"] = mapping.external_port
            mutated = True

    if not mutated:
        return compose_content

    sink = StringIO()
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.dump(payload, sink)
    return sink.getvalue()


def _port_id_for_entry(
    stack_name: str,
    service_name: str,
    port_entry: Mapping[object, object],
) -> str | None:
    target = port_entry.get("target")
    if not isinstance(target, int):
        return None
    return _DIRECT_PUBLISHED_PORT_IDS.get((stack_name, service_name, target))


_DIRECT_PUBLISHED_PORT_IDS: dict[tuple[str, str, int], str] = {
    ("portainer", "portainer", 9000): "portainer-http",
    ("jenkins", "jenkins", 8080): "jenkins-http",
    ("jenkins", "jenkins", 50000): "jenkins-agent",
    ("nexus", "nexus", 8081): "nexus-http",
    ("nexus", "nexus", 5000): "nexus-docker-http",
    ("nexus", "nexus", 5001): "nexus-docker-https",
    ("infisical", "infisical", 8080): "infisical-http",
    ("pulsar", "pulsar", 6650): "pulsar-broker",
    ("pulsar", "pulsar", 8080): "pulsar-admin-api",
    ("pulsar", "pulsar-manager", 9527): "pulsar-manager-gui",
    ("sonarqube", "sonarqube", 9000): "sonarqube-http",
    ("swagger", "swagger-ui", 8080): "swagger-ui",
    ("swagger", "swagger-nginx", 8084): "openapi-aggregator",
    ("traefik", "traefik", 80): "api-gateway-http",
    ("traefik", "traefik", 443): "api-gateway-https",
}
