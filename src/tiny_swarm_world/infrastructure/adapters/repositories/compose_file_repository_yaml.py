import re
from collections.abc import Mapping
from pathlib import Path

from ruamel.yaml import YAML

from tiny_swarm_world.application.ports.repositories.port_compose_file_repository import PortComposeFileRepository
from tiny_swarm_world.domain.deployment.stack_definition import (
    ComposeServiceDefinition,
    StackDefinition,
)
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory
from tiny_swarm_world.infrastructure.project_paths import infra_root


STACK_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")
_YAML = YAML(typ="safe")


class ComposeFileRepositoryYaml(PortComposeFileRepository):
    def __init__(self, base_directories: list[Path] | None = None):
        root = infra_root()
        self.base_directories = base_directories or [
            root / "config" / "compose",
        ]
        self.logger = LoggerFactory.get_logger(self.__class__)

    def get_compose_of(self, stack_name: str) -> StackDefinition:
        if not STACK_NAME_PATTERN.fullmatch(stack_name):
            raise ValueError("compose stack name contains invalid characters")

        for base_directory in self.base_directories:
            for compose_path in self._compose_paths_for(base_directory, stack_name):
                self.logger.info("Loaded compose file for stack '%s'.", stack_name)
                return StackDefinition(
                    name=stack_name,
                    compose_content=compose_path.read_text(encoding="utf-8"),
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
