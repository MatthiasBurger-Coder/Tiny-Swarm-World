"""Project Compose host-port publication from the selected exposure policy.

The repository owns YAML I/O; this policy owns internal publication removal and
canonical direct-port assignment on an already validated Compose payload.
"""
from collections.abc import Mapping
from typing import Any

from tiny_swarm_world.application.ports.repositories.port_repository_failure import RepositoryConfigurationError
from tiny_swarm_world.domain.lifecycle.exposure import service_exposure_for
from tiny_swarm_world.domain.network import PortRegistry, ServicePortMapping
from tiny_swarm_world.infrastructure.adapters.repositories.swagger_exposure import internal_swagger_payload


class ComposePortExposure:
    def __init__(
        self,
        resolved_services: tuple[str, ...] | None,
        service_exposure: Mapping[str, str] | None,
        port_registry: PortRegistry,
    ) -> None:
        self.service_exposure = service_exposure_for(resolved_services, service_exposure)
        self._ports_by_id = {mapping.port_id: mapping for mapping in port_registry.mappings}

    def apply(self, stack_name: str, payload: dict[str, Any]) -> bool:
        """Return whether the validated payload needs serialization after projection."""
        if stack_name == 'swagger' and self.service_exposure.get('swagger') == 'internal':
            internal_swagger_payload(payload)
            return True
        return _apply_direct_published_ports(stack_name, payload['services'], self._ports_by_id)


def _apply_direct_published_ports(
    stack_name: str,
    services: Mapping[object, object],
    ports_by_id: Mapping[str, ServicePortMapping],
) -> bool:
    mutated = False
    for service_name, service_payload in services.items():
        if not isinstance(service_name, str) or not isinstance(service_payload, Mapping):
            continue
        configured_ports = service_payload.get("ports")
        if not isinstance(configured_ports, list):
            continue

        for entry in configured_ports:
            mutated = _apply_direct_published_port(
                stack_name,
                service_name,
                entry,
                ports_by_id,
            ) or mutated
    return mutated


def _apply_direct_published_port(
    stack_name: str,
    service_name: str,
    entry: object,
    ports_by_id: Mapping[str, ServicePortMapping],
) -> bool:
    if not isinstance(entry, dict):
        return False
    port_id = _port_id_for_entry(stack_name, service_name, entry)
    if port_id is None:
        return False
    mapping = ports_by_id.get(port_id)
    if mapping is None:
        raise RepositoryConfigurationError(f"direct port '{port_id}' is missing from the port registry")
    if mapping.external_port is None:
        return False
    if entry.get("published") == mapping.external_port:
        return False
    entry["published"] = mapping.external_port
    return True


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
    ("service-access", "service-access-nginx", 80): "service-access-http",
    ("pulsar", "pulsar", 6650): "pulsar-broker",
    ("pulsar", "pulsar", 8080): "pulsar-admin-api",
    ("pulsar", "pulsar-manager", 9527): "pulsar-manager-gui",
    ("sonarqube", "sonarqube", 9000): "sonarqube-http",
    ("swagger", "swagger-ui", 8080): "swagger-ui",
    ("swagger", "swagger-nginx", 8084): "openapi-aggregator",
    ("traefik", "traefik", 80): "traefik-http",
    ("traefik", "traefik", 443): "traefik-https",
}
