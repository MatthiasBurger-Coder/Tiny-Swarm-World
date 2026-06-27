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
    "api": ("api", "tiny-swarm", 8081),
    "app": ("app", "tiny-swarm", 8080),
    "grafana": ("grafana", "grafana", 3000),
    "infisical": ("infisical", "infisical", 8080),
    "jenkins": ("jenkins", "jenkins", 8080),
    "nexus": ("nexus", "nexus", 8081),
    "portainer": ("portainer", "portainer", 9000),
    "prometheus": ("prometheus", "prometheus", 9090),
    "pulsar-admin-api": ("pulsar-api", "pulsar", 8080),
    "pulsar-manager": ("pulsar", "pulsar-manager", 9527),
    "service-access": ("service-access", "service-access-dashboard", 80),
    "sonarqube": ("sonarqube", "sonarqube", 9000),
    "swagger": ("swagger", "swagger-nginx", 8084),
}

_ROUTED_HEALTH_PATHS = {
    "pulsar-admin-api": "/admin/v2/clusters",
}

_DIAGNOSTIC_FALLBACK_PORTS = (
    ("api-gateway-http", "api-gateway", 10080, "diagnostic"),
    ("api-gateway-https", "api-gateway", 10443, "diagnostic"),
    ("service-access-http", "service-access", 10000, "diagnostic"),
    ("portainer-http", "portainer", 10001, "compatibility"),
    ("jenkins-http", "jenkins", 11080, "diagnostic"),
    ("jenkins-agent", "jenkins", 11050, "diagnostic"),
    ("sonarqube-http", "sonarqube", 12000, "diagnostic"),
    ("nexus-http", "nexus", 13081, "diagnostic"),
    ("nexus-docker-http", "nexus", 13500, "diagnostic"),
    ("nexus-docker-https", "nexus", 13501, "diagnostic"),
    ("pulsar-broker", "pulsar", 14001, "diagnostic"),
    ("pulsar-admin-api", "pulsar", 14080, "diagnostic"),
    ("pulsar-manager-gui", "pulsar", 14081, "diagnostic"),
    ("prometheus-http", "prometheus", 15090, "diagnostic"),
    ("grafana-http", "grafana", 15300, "diagnostic"),
    ("swagger-ui", "swagger", 16080, "diagnostic"),
    ("openapi-aggregator", "swagger", 16081, "diagnostic"),
    ("infisical-http", "infisical", 17080, "diagnostic"),
    ("tiny-swarm-frontend", "tiny-swarm", 18080, "diagnostic"),
    ("tiny-swarm-backend", "tiny-swarm", 18081, "diagnostic"),
)

_ROUTE_CANDIDATES = frozenset(
    {
        "api",
        "app",
        "grafana",
        "infisical",
        "jenkins",
        "nexus",
        "portainer",
        "prometheus",
        "pulsar-admin-api",
        "pulsar-manager",
        "service-access",
        "sonarqube",
        "swagger",
    }
)


@dataclass(frozen=True)
class DesiredHttpsRoute:
    service_name: str
    hostname: str
    upstream_service: str
    upstream_port: int
    profile_member: bool = True
    health_check_url: str = ""
    service_access_url: str = ""

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
        service_access_url = self.service_access_url or f"https://{self.hostname}"
        health_check_url = self.health_check_url or (
            service_access_url + _ROUTED_HEALTH_PATHS.get(self.service_name, "")
        )
        return {
            "health_check_url": health_check_url,
            "hostname": self.hostname,
            "profile_member": self.profile_member,
            "service_name": self.service_name,
            "service_access_url": service_access_url,
            "upstream_port": self.upstream_port,
            "upstream_service": self.upstream_service,
        }


@dataclass(frozen=True)
class DiagnosticFallbackPort:
    port_id: str
    service_name: str
    port: int
    classification: str

    def to_dict(self) -> dict[str, object]:
        return {
            "classification": self.classification,
            "port": self.port,
            "port_id": self.port_id,
            "service": self.service_name,
        }


@dataclass(frozen=True)
class SkippedRoute:
    service_name: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"reason": self.reason, "service": self.service_name}


@dataclass(frozen=True)
class DesiredHttpsIngress:
    routes: tuple[DesiredHttpsRoute, ...]
    diagnostic_fallback_ports: tuple[DiagnosticFallbackPort, ...] = ()
    skipped_routes: tuple[SkippedRoute, ...] = ()
    public_ports: tuple[int, ...] = (80, 443)
    http_redirect_to_https: bool = True
    exposed_by_default: bool = False
    api_insecure: bool = False
    service_access_preferred_url_source: str = "traefik_host_route"

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
        object.__setattr__(
            self,
            "diagnostic_fallback_ports",
            tuple(self.diagnostic_fallback_ports),
        )
        object.__setattr__(self, "skipped_routes", tuple(self.skipped_routes))
        object.__setattr__(self, "public_ports", tuple(self.public_ports))

    @property
    def hostnames(self) -> tuple[str, ...]:
        return tuple(route.hostname for route in self.routes)

    def to_dict(self) -> dict[str, object]:
        return {
            "api_insecure": self.api_insecure,
            "diagnostic_fallback_ports": [
                fallback.to_dict() for fallback in self.diagnostic_fallback_ports
            ],
            "exposed_by_default": self.exposed_by_default,
            "gateway_public_ingress_ports": list(self.public_ports),
            "http_redirect_to_https": self.http_redirect_to_https,
            "health_check_targets": [
                {
                    "service": route.service_name,
                    "target": route.to_dict()["health_check_url"],
                    "upstream_port": route.upstream_port,
                    "upstream_service": route.upstream_service,
                }
                for route in self.routes
            ],
            "public_ports": list(self.public_ports),
            "routes": [route.to_dict() for route in self.routes],
            "service_access_links": [
                {
                    "preferred": True,
                    "service": route.service_name,
                    "url": route.to_dict()["service_access_url"],
                }
                for route in self.routes
            ],
            "service_access_preferred_url_source": self.service_access_preferred_url_source,
            "skipped_routes": [skipped.to_dict() for skipped in self.skipped_routes],
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
    profile_endpoint_names: set[str] = set()
    for contract in service_stack_contracts_for_profile(service_profile):
        for endpoint in contract.endpoints:
            profile_endpoint_names.add(endpoint.name)
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
        if service_name in _ROUTE_OVERRIDES and not any(
            route.service_name == service_name for route in routes
        ):
            hostname_service, upstream_service, upstream_port = _route_values_for(
                service_name,
                service_name,
                443,
            )
            routes.append(
                DesiredHttpsRoute(
                    service_name=service_name,
                    hostname=f"{hostname_service}.{base_domain}",
                    upstream_service=upstream_service,
                    upstream_port=upstream_port,
                    profile_member=service_name in profile_endpoint_names,
                )
            )
    skipped_routes = _skipped_routes(selected_services, profile_endpoint_names)
    return DesiredHttpsIngress(
        routes=tuple(routes),
        diagnostic_fallback_ports=tuple(
            DiagnosticFallbackPort(
                port_id=port_id,
                service_name=service_name,
                port=port,
                classification=classification,
            )
            for port_id, service_name, port, classification in _DIAGNOSTIC_FALLBACK_PORTS
        ),
        skipped_routes=skipped_routes,
    )


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


def _skipped_routes(
    selected_services: set[str],
    profile_endpoint_names: set[str],
) -> tuple[SkippedRoute, ...]:
    skipped: list[SkippedRoute] = [SkippedRoute("rabbitmq", "service_not_supported")]
    for service_name in sorted(_ROUTE_CANDIDATES - selected_services):
        skipped.append(SkippedRoute(service_name, "service_not_enabled"))
    for service_name in sorted(selected_services - profile_endpoint_names):
        if service_name not in _DEFAULT_HTTPS_ROUTE_SERVICES:
            skipped.append(SkippedRoute(service_name, "service_not_in_active_profile"))
    return tuple(skipped)
