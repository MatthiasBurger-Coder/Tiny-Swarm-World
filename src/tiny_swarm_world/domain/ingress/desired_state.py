from __future__ import annotations

import re
from dataclasses import dataclass

from tiny_swarm_world.domain.deployment import (
    ServiceStackProfile,
    service_stack_contracts_for_profile,
)
from tiny_swarm_world.domain.ingress.discovery import validate_ingress_summary_text

_SERVICE_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_HOSTNAME_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)
_DEFAULT_HTTPS_ROUTE_SERVICES = frozenset(
    {
        "infisical",
        "jenkins",
        "nexus",
        "portainer",
        "pulsar-admin-api",
        "pulsar-manager",
        "service-access",
        "sonarqube",
        "swagger",
    }
)

_ROUTE_OVERRIDES = {
    "infisical": ("infisical", "infisical", 8080),
    "jenkins": ("jenkins", "jenkins", 8080),
    "nexus": ("nexus", "nexus", 8081),
    "portainer": ("portainer", "portainer", 9000),
    "pulsar-admin-api": ("pulsar-api", "pulsar", 8080),
    "pulsar-manager": ("pulsar", "pulsar-manager", 9527),
    "service-access": ("service-access", "service-access-dashboard", 80),
    "sonarqube": ("sonarqube", "sonarqube", 9000),
    "swagger": ("swagger", "swagger-nginx", 8084),
}


@dataclass(frozen=True)
class DesiredHttpsRoute:
    service_name: str
    hostname: str
    upstream_service: str
    upstream_port: int

    def __post_init__(self) -> None:
        for field_name, value in (
            ("service_name", self.service_name),
            ("upstream_service", self.upstream_service),
        ):
            validate_ingress_summary_text(field_name, value)
            if not _SERVICE_IDENTIFIER_PATTERN.fullmatch(value):
                raise ValueError(f"{field_name} must be a lowercase service identifier")
        validate_ingress_summary_text("hostname", self.hostname)
        if not _HOSTNAME_PATTERN.fullmatch(self.hostname):
            raise ValueError("hostname must be a lowercase DNS hostname")
        if not 1 <= self.upstream_port <= 65535:
            raise ValueError("upstream port must be in the valid TCP port range")

    def to_dict(self) -> dict[str, object]:
        return {
            "hostname": self.hostname,
            "service_name": self.service_name,
            "upstream_port": self.upstream_port,
            "upstream_service": self.upstream_service,
        }


@dataclass(frozen=True)
class DesiredHttpsIngress:
    routes: tuple[DesiredHttpsRoute, ...]
    public_ports: tuple[int, ...] = (80, 443)
    http_redirect_to_https: bool = True
    exposed_by_default: bool = False
    api_insecure: bool = False

    def __post_init__(self) -> None:
        routes = tuple(self.routes)
        if not routes:
            raise ValueError("desired HTTPS ingress requires at least one route")
        hostnames = tuple(route.hostname for route in routes)
        if len(set(hostnames)) != len(hostnames):
            raise ValueError("desired HTTPS ingress hostnames must be unique")
        if tuple(self.public_ports) != (80, 443):
            raise ValueError("desired HTTPS ingress public ports must be exactly 80 and 443")
        if not self.http_redirect_to_https:
            raise ValueError("desired HTTPS ingress must redirect HTTP to HTTPS")
        if self.exposed_by_default:
            raise ValueError("desired HTTPS ingress must set exposedByDefault=false")
        if self.api_insecure:
            raise ValueError("Traefik insecure API mode is forbidden")
        object.__setattr__(self, "routes", routes)
        object.__setattr__(self, "public_ports", tuple(self.public_ports))

    @property
    def hostnames(self) -> tuple[str, ...]:
        return tuple(route.hostname for route in self.routes)

    def to_dict(self) -> dict[str, object]:
        return {
            "api_insecure": self.api_insecure,
            "exposed_by_default": self.exposed_by_default,
            "http_redirect_to_https": self.http_redirect_to_https,
            "public_ports": list(self.public_ports),
            "routes": [route.to_dict() for route in self.routes],
        }


def desired_https_ingress_for_profile(
    service_profile: ServiceStackProfile | str = ServiceStackProfile.SERVICE_ACCESS,
    *,
    base_domain: str = "tsw.local",
    conditional_service_names: tuple[str, ...] = (),
) -> DesiredHttpsIngress:
    selected_services = set(_DEFAULT_HTTPS_ROUTE_SERVICES)
    selected_services.update(conditional_service_names)
    routes: list[DesiredHttpsRoute] = []
    for contract in service_stack_contracts_for_profile(service_profile):
        for endpoint in contract.endpoints:
            if endpoint.name not in selected_services:
                continue
            hostname_service, upstream_service, upstream_port = _route_values_for(
                endpoint.name,
                contract.required_services[0],
                _endpoint_port(endpoint.url),
            )
            routes.append(
                DesiredHttpsRoute(
                    service_name=endpoint.name,
                    hostname=f"{hostname_service}.{base_domain}",
                    upstream_service=upstream_service,
                    upstream_port=upstream_port,
                )
            )
    for service_name in conditional_service_names:
        if service_name == "grafana" and not any(
            route.service_name == "grafana" for route in routes
        ):
            routes.append(
                DesiredHttpsRoute(
                    service_name="grafana",
                    hostname=f"grafana.{base_domain}",
                    upstream_service="grafana",
                    upstream_port=3000,
                )
            )
    return DesiredHttpsIngress(routes=tuple(routes))


def _route_values_for(
    endpoint_name: str,
    default_upstream_service: str,
    default_upstream_port: int,
) -> tuple[str, str, int]:
    return _ROUTE_OVERRIDES.get(
        endpoint_name,
        (endpoint_name, default_upstream_service, default_upstream_port),
    )


def _endpoint_port(url: str) -> int:
    port_text = url.rsplit(":", maxsplit=1)[-1]
    if port_text.isdigit():
        return int(port_text)
    return 443 if url.startswith("https://") else 80
