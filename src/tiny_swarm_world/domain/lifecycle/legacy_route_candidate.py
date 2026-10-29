"""Unverified pure rendering of the existing legacy published route mapping."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

from tiny_swarm_world.domain.lifecycle.manifest_v2 import SwaggerExposure, UnknownIdentity, preview_migration
from tiny_swarm_world.domain.preflight.setup_manifest import SetupProfile, default_setup_manifest


class SourceContext(Enum):
    """Caller statement about applicability; not independently verified."""

    STOCK_LEGACY = "stock_legacy"
    CUSTOM_OVERRIDE = "custom_override"
    ALTERNATE_INFRA = "alternate_infra"
    UNKNOWN = "unknown"


class CandidateStatus(Enum):
    CANDIDATE = "CANDIDATE"
    AUTHORITY_GAP = "AUTHORITY_GAP"


@dataclass(frozen=True, slots=True)
class RouteInputs:
    listen_address: str
    gateway_node: str


@dataclass(frozen=True, slots=True)
class LegacyRoute:
    service: str
    listen_port: int
    target_port: int
    listen_address: str
    target_address: str
    gateway_node: str
    device_name: str
    nat: UnknownIdentity = UnknownIdentity.UNKNOWN
    proxy_protocol: UnknownIdentity = UnknownIdentity.UNKNOWN


@dataclass(frozen=True, slots=True)
class LegacyCandidate:
    status: CandidateStatus
    installation_id: str | None = None
    routes: tuple[LegacyRoute, ...] = ()
    source: str = "legacy_setup_code_unverified_runtime"
    applied: bool = False
    qualified: bool = False
    host: UnknownIdentity = UnknownIdentity.UNKNOWN
    project: UnknownIdentity = UnknownIdentity.UNKNOWN
    profile: UnknownIdentity = UnknownIdentity.UNKNOWN
    ownership: UnknownIdentity = UnknownIdentity.UNKNOWN


_GAP = LegacyCandidate(status=CandidateStatus.AUTHORITY_GAP)
_SERVICE_IDS = frozenset({"incus", "portainer", "nexus", "jenkins", "pulsar", "sonarqube",
                          "swagger", "traefik", "infisical", "service-access"})
_GATEWAY = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*", re.ASCII)
# Review-bound compatibility pairs. Unknown labels or changed port mappings
# require a separate policy review rather than being treated as established.
_ALLOWED_PORTS = frozenset({
    (10001, "Portainer"), (13081, "Nexus"), (13500, "Nexus Docker registry"),
    (13501, "Nexus Docker proxy registry"), (11080, "Jenkins"),
    (11050, "Jenkins inbound agent"), (14001, "Pulsar broker protocol"),
    (14080, "Pulsar Admin API"), (14081, "Pulsar Manager UI"),
    (7750, "Pulsar Manager backend"), (12000, "SonarQube"),
    (16080, "Swagger UI"), (16081, "Swagger/NGINX"),
    (80, "Traefik HTTP ingress"), (443, "Traefik HTTPS ingress"),
    (10000, "Service Access"), (8086, "Infisical legacy route"), (17080, "Infisical"),
})


def legacy_route_candidate(manifest: object, catalog: object, *, source: object,
                           exposure: object, inputs: object) -> LegacyCandidate:
    """Return an unverified candidate or one fixed authority-gap result."""
    try:
        if (source is not SourceContext.STOCK_LEGACY or exposure is not SwaggerExposure.PUBLISHED
                or type(inputs) is not RouteInputs or type(inputs.listen_address) is not str
                or inputs.listen_address not in {"127.0.0.1", "0.0.0.0"}
                or type(inputs.gateway_node) is not str or _GATEWAY.fullmatch(inputs.gateway_node) is None):
            return _GAP
        validated = preview_migration(manifest, catalog)
        snapshot = validated.v1_snapshot
        preset = snapshot["service_preset"]
        selected = snapshot["resolved_services"]
        installation_id = snapshot["installation_id"]
        if (type(preset) is not str or type(selected) is not tuple or type(installation_id) is not str
                or any(type(name) is not str or name not in _SERVICE_IDS for name in selected)):
            return _GAP
        setup = default_setup_manifest(profile=SetupProfile.FULL, service_profile=preset,
                                       resolved_services=selected)
        routes = []
        seen_ports: set[int] = set()
        seen_devices: set[str] = set()
        for requirement in setup.required_ports:
            port, service = requirement.port, requirement.service
            if (type(port) is not int or not 1 <= port <= 65535 or type(service) is not str
                    or (port, service) not in _ALLOWED_PORTS):
                return _GAP
            device = f"tsw-proxy-{port}"
            if port in seen_ports or device in seen_devices:
                return _GAP
            seen_ports.add(port)
            seen_devices.add(device)
            routes.append(LegacyRoute(service=service, listen_port=port, target_port=port,
                                      listen_address=inputs.listen_address, target_address="127.0.0.1",
                                      gateway_node=inputs.gateway_node, device_name=device))
        return LegacyCandidate(status=CandidateStatus.CANDIDATE, installation_id=installation_id,
                               routes=tuple(sorted(routes, key=lambda item: (item.listen_port, item.service))))
    except Exception:
        return _GAP
