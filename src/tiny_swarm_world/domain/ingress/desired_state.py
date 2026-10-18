from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from tiny_swarm_world.domain.deployment import (
    ServiceStackProfile,
    service_stack_contracts_for_profile,
)
from tiny_swarm_world.domain.ingress.discovery import validate_ingress_summary_text
from tiny_swarm_world.domain.network import PortExposureClass, PortRegistry, ServicePortMapping

_SERVICE_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_HOSTNAME_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)


@dataclass(frozen=True)
class CredentialReference:
    username_label: str
    item_reference: str
    note: str

    def to_dict(self) -> dict[str, str]:
        return {
            "item_reference": self.item_reference,
            "note": self.note,
            "username_label": self.username_label,
        }


@dataclass(frozen=True)
class RouteDefinition:
    route_name: str
    hostname_prefix: str
    upstream_service: str
    upstream_port: int
    enabled_by_default: bool = False
    health_path: str = ""
    service_access_path: str = ""
    credential: CredentialReference | None = None
    no_login_note: str = ""

    def __post_init__(self) -> None:
        for field_name, value in (
            ("route_name", self.route_name),
            ("hostname_prefix", self.hostname_prefix),
            ("upstream_service", self.upstream_service),
        ):
            validate_ingress_summary_text(field_name, value)
            if not _SERVICE_IDENTIFIER_PATTERN.fullmatch(value):
                raise ValueError(f"{field_name} must be a lowercase service identifier")
        if not 1 <= self.upstream_port <= 65535:
            raise ValueError("upstream port must be in the valid TCP port range")


@dataclass(frozen=True)
class DesiredHttpsRoute:
    service_name: str
    hostname: str
    upstream_service: str
    upstream_port: int
    profile_member: bool = True
    health_check_url: str = ""
    service_access_url: str = ""
    credential: CredentialReference | None = None
    no_login_note: str = ""

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
        base_url = f"https://{self.hostname}"
        service_access_url = self.service_access_url or base_url
        health_check_url = self.health_check_url or base_url
        route: dict[str, object] = {
            "health_check_url": health_check_url,
            "hostname": self.hostname,
            "profile_member": self.profile_member,
            "service_name": self.service_name,
            "service_access_url": service_access_url,
            "upstream_port": self.upstream_port,
            "upstream_service": self.upstream_service,
        }
        if self.credential is not None:
            route["credential"] = self.credential.to_dict()
        if self.no_login_note:
            route["no_login_note"] = self.no_login_note
        return route


@dataclass(frozen=True)
class DirectServiceEndpoint:
    service_name: str
    service_access_url: str
    health_check_url: str
    upstream_service: str
    upstream_port: int
    credential: CredentialReference | None = None
    no_login_note: str = ""

    def __post_init__(self) -> None:
        for value in (self.service_name, self.upstream_service):
            if not _SERVICE_IDENTIFIER_PATTERN.fullmatch(value):
                raise ValueError("direct endpoint requires a lowercase service identifier")
        if not 1 <= self.upstream_port <= 65535:
            raise ValueError("direct endpoint upstream port is invalid")
        for url in (self.service_access_url, self.health_check_url):
            validate_ingress_summary_text("direct endpoint URL", url)
            parsed = urlsplit(url)
            if (
                parsed.scheme != "http" or parsed.hostname != "localhost"
                or parsed.username is not None or parsed.password is not None
                or parsed.query or parsed.fragment or parsed.port is None or not 1 <= parsed.port <= 65535
            ):
                raise ValueError("direct endpoint URL must use localhost HTTP with a port")

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "service_name": self.service_name,
            "service_access_url": self.service_access_url,
            "health_check_url": self.health_check_url,
            "upstream_service": self.upstream_service,
            "upstream_port": self.upstream_port,
        }
        if self.credential is not None:
            payload["credential"] = self.credential.to_dict()
        if self.no_login_note:
            payload["no_login_note"] = self.no_login_note
        return payload


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
    gateway_enabled: bool = True
    direct_endpoints: tuple[DirectServiceEndpoint, ...] = ()

    def __post_init__(self) -> None:
        routes = tuple(self.routes)
        if self.gateway_enabled and not routes:
            raise ValueError("desired HTTPS ingress requires at least one route")
        hostnames = tuple(route.hostname for route in routes)
        if len(set(hostnames)) != len(hostnames):
            raise ValueError("desired HTTPS ingress hostnames must be unique")
        if self.gateway_enabled and tuple(self.public_ports) != (80, 443):
            raise ValueError("desired HTTPS ingress public ports must be exactly 80 and 443")
        if self.gateway_enabled and not self.http_redirect_to_https:
            raise ValueError("desired HTTPS ingress must redirect HTTP to HTTPS")
        if not self.gateway_enabled and (routes or self.public_ports or self.http_redirect_to_https):
            raise ValueError("disabled gateway must not advertise routes, ports or redirects")
        if self.gateway_enabled and self.direct_endpoints:
            raise ValueError("enabled gateway must use HTTPS routes")
        object.__setattr__(self, "direct_endpoints", tuple(self.direct_endpoints))
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
        access_endpoints: tuple[DesiredHttpsRoute | DirectServiceEndpoint, ...] = (*self.routes, *self.direct_endpoints)
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
                for route in access_endpoints
            ],
            "public_ports": list(self.public_ports),
            "routes": [route.to_dict() for route in self.routes],
            "service_access_links": [
                _service_access_link_for_route(route)
                for route in access_endpoints
            ],
            "service_access_preferred_url_source": self.service_access_preferred_url_source,
            "skipped_routes": [skipped.to_dict() for skipped in self.skipped_routes],
        }


def _service_access_link_for_route(route: DesiredHttpsRoute | DirectServiceEndpoint) -> dict[str, object]:
    route_payload = route.to_dict()
    link: dict[str, object] = {
        "preferred": True,
        "service": route.service_name,
        "url": route_payload["service_access_url"],
    }
    if "credential" in route_payload:
        link["credential"] = route_payload["credential"]
    if "no_login_note" in route_payload:
        link["no_login_note"] = route_payload["no_login_note"]
    return link


def desired_https_ingress_for_profile(
    service_profile: ServiceStackProfile | str = ServiceStackProfile.SERVICE_ACCESS,
    *,
    base_domain: str = "tsw.local",
    conditional_service_names: tuple[str, ...] = (),
    port_registry: PortRegistry | None = None,
    resolved_services: tuple[str, ...] | None = None,
) -> DesiredHttpsIngress:
    if resolved_services is not None and port_registry is not None:
        metadata = dict(port_registry.metadata or {})
        metadata["unsupported_routes"] = ",".join(
            name for name in _unsupported_routes(port_registry) if name in resolved_services
        )
        port_registry = PortRegistry(
            ranges=port_registry.ranges,
            mappings=tuple(
                mapping for mapping in port_registry.mappings
                if mapping.service_id in resolved_services
            ),
            metadata=metadata,
        )
    if resolved_services is not None and "traefik" not in resolved_services:
        return _direct_access_for_selection(service_profile, port_registry, resolved_services)
    route_registry = _route_registry(port_registry)
    selected_services = {
        route_name
        for route_name, definition in route_registry.items()
        if definition.enabled_by_default
    }
    conditional_service_names = tuple(
        name for name in conditional_service_names if name in route_registry
    ) if resolved_services is not None else conditional_service_names
    selected_services.update(conditional_service_names)
    routes: list[DesiredHttpsRoute] = []
    profile_endpoint_names: set[str] = set()
    for contract in service_stack_contracts_for_profile(service_profile):
        if resolved_services is not None and contract.stack_name not in resolved_services:
            continue
        for endpoint in contract.endpoints:
            profile_endpoint_names.add(endpoint.name)
            if endpoint.name not in selected_services:
                continue
            route_definition = route_registry.get(endpoint.name)
            if route_definition is None:
                continue
            routes.append(
                DesiredHttpsRoute(
                    service_name=endpoint.name,
                    hostname=f"{route_definition.hostname_prefix}.{base_domain}",
                    upstream_service=route_definition.upstream_service,
                    upstream_port=route_definition.upstream_port,
                    health_check_url=_url_for_path(route_definition, base_domain, "health"),
                    service_access_url=_url_for_path(route_definition, base_domain, "access"),
                    credential=route_definition.credential,
                    no_login_note=route_definition.no_login_note,
                )
            )
    for service_name in conditional_service_names:
        route_definition = route_registry.get(service_name)
        if route_definition is not None and not any(
            route.service_name == service_name for route in routes
        ):
            routes.append(
                DesiredHttpsRoute(
                    service_name=service_name,
                    hostname=f"{route_definition.hostname_prefix}.{base_domain}",
                    upstream_service=route_definition.upstream_service,
                    upstream_port=route_definition.upstream_port,
                    health_check_url=_url_for_path(route_definition, base_domain, "health"),
                    service_access_url=_url_for_path(route_definition, base_domain, "access"),
                    profile_member=service_name in profile_endpoint_names,
                    credential=route_definition.credential,
                    no_login_note=route_definition.no_login_note,
                )
            )
    unsupported_routes = _unsupported_routes(port_registry)
    active_route_names = {route.service_name for route in routes}
    skipped_routes = _skipped_routes(
        selected_services,
        active_route_names,
        set(route_registry),
        unsupported_routes,
    )
    return DesiredHttpsIngress(
        routes=tuple(routes),
        diagnostic_fallback_ports=_diagnostic_fallback_ports(port_registry),
        skipped_routes=skipped_routes,
    )


def _direct_access_for_selection(
    service_profile: ServiceStackProfile | str,
    port_registry: PortRegistry | None,
    resolved_services: tuple[str, ...],
) -> DesiredHttpsIngress:
    endpoints: list[DirectServiceEndpoint] = []
    endpoint_names = {
        endpoint.name
        for contract in service_stack_contracts_for_profile(service_profile)
        if contract.stack_name in resolved_services
        for endpoint in contract.endpoints
    }
    for mapping in port_registry.mappings if port_registry is not None else ():
        definition = _route_definition_from_mapping(mapping)
        if definition is None or definition.route_name not in endpoint_names or mapping.external_port is None:
            continue
        base_url = f"http://localhost:{mapping.external_port}"
        endpoints.append(DirectServiceEndpoint(
            service_name=definition.route_name,
            service_access_url=f"{base_url}{definition.service_access_path}",
            health_check_url=f"{base_url}{definition.health_path}",
            upstream_service=definition.upstream_service,
            upstream_port=definition.upstream_port,
            credential=definition.credential,
            no_login_note=definition.no_login_note,
        ))
    return DesiredHttpsIngress(
        routes=(), gateway_enabled=False, direct_endpoints=tuple(endpoints),
        public_ports=(), http_redirect_to_https=False,
        diagnostic_fallback_ports=_diagnostic_fallback_ports(port_registry),
        service_access_preferred_url_source="direct_published_port",
    )


def _url_for_path(route_definition: RouteDefinition, base_domain: str, path_kind: str) -> str:
    path = (
        route_definition.health_path
        if path_kind == "health"
        else route_definition.service_access_path
    )
    return f"https://{route_definition.hostname_prefix}.{base_domain}{path}"


def _skipped_routes(
    selected_services: set[str],
    active_route_names: set[str],
    route_candidates: set[str],
    unsupported_routes: tuple[str, ...],
) -> tuple[SkippedRoute, ...]:
    skipped: list[SkippedRoute] = [
        SkippedRoute(service_name, "service_not_supported")
        for service_name in unsupported_routes
    ]
    for service_name in sorted(route_candidates - selected_services):
        skipped.append(SkippedRoute(service_name, "service_not_enabled"))
    for service_name in sorted(
        (selected_services & route_candidates) - active_route_names
    ):
        skipped.append(SkippedRoute(service_name, "service_not_in_active_profile"))
    return tuple(skipped)


def _unsupported_routes(port_registry: PortRegistry | None) -> tuple[str, ...]:
    if port_registry is None:
        return ()
    return tuple(
        route.strip()
        for route in str((port_registry.metadata or {}).get("unsupported_routes", "")).split(",")
        if route.strip()
    )


def _route_registry(port_registry: PortRegistry | None) -> dict[str, RouteDefinition]:
    if port_registry is None:
        return {}
    routes: dict[str, RouteDefinition] = {}
    for mapping in port_registry.mappings:
        route_definition = _route_definition_from_mapping(mapping)
        if route_definition is not None:
            routes[route_definition.route_name] = route_definition
    return routes


def _route_definition_from_mapping(mapping: ServicePortMapping) -> RouteDefinition | None:
    if mapping.route_host is None:
        return None
    metadata = dict(mapping.metadata or {})
    route_name = metadata.get("route_name", _default_route_name_for_mapping(mapping))
    if route_name == "none":
        return None
    upstream_service = metadata.get("upstream_service", mapping.service_id)
    return RouteDefinition(
        route_name=route_name,
        hostname_prefix=mapping.route_host.split(".", maxsplit=1)[0],
        upstream_service=upstream_service,
        upstream_port=mapping.internal_port,
        enabled_by_default=metadata.get("route_enabled_by_default") == "true",
        health_path=metadata.get("health_path", ""),
        service_access_path=metadata.get("service_access_path", metadata.get("health_path", "")),
        credential=_credential_from_metadata(metadata),
        no_login_note=metadata.get("no_login_note", ""),
    )


def _default_route_name_for_mapping(mapping: ServicePortMapping) -> str:
    if mapping.port_id.endswith("-http"):
        return mapping.port_id.removesuffix("-http")
    return mapping.port_id


def _credential_from_metadata(metadata: dict[str, str]) -> CredentialReference | None:
    item_reference = metadata.get("credential_item_ref")
    if item_reference is None:
        return None
    return CredentialReference(
        username_label=metadata.get("credential_user", "admin"),
        item_reference=item_reference,
        note=metadata.get("credential_note", "View secret in Infisical"),
    )


def _diagnostic_fallback_ports(
    port_registry: PortRegistry | None,
) -> tuple[DiagnosticFallbackPort, ...]:
    if port_registry is None:
        return ()
    fallback_exposures = {
        PortExposureClass.COMPATIBILITY,
        PortExposureClass.DIAGNOSTIC,
        PortExposureClass.DIRECT,
    }
    return tuple(
        DiagnosticFallbackPort(
            port_id=mapping.port_id,
            service_name=mapping.service_id,
            port=mapping.external_port,
            classification=mapping.exposure.value,
        )
        for mapping in port_registry.mappings
        if mapping.external_port is not None and mapping.exposure in fallback_exposures
    )
