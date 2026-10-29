"""Pure ideal scoped route reference; actual runtime source stays unknown."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
from uuid import UUID

from tiny_swarm_world.domain.lifecycle.manifest_v2 import UnknownIdentity, preview_migration
from tiny_swarm_world.domain.lifecycle.models import ComponentCatalog
from tiny_swarm_world.domain.preflight.setup_manifest import SetupProfile, default_setup_manifest


class SwaggerMode(Enum):
    PUBLISHED = "published"
    INTERNAL = "internal"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"


class PolicyStatus(Enum):
    REFERENCE = "REFERENCE"
    AUTHORITY_GAP = "AUTHORITY_GAP"


@dataclass(frozen=True, slots=True)
class ScopedRoute:
    service_id: str
    device_name: str
    protocol: str
    listen_address: str
    listen_port: int
    connect_address: str
    connect_port: int
    bind: str
    nat: bool
    proxy_protocol: bool


@dataclass(frozen=True, slots=True)
class ScopedPolicyReference:
    status: PolicyStatus
    installation_id: str | None = None
    profile_name: str | None = None
    routes: tuple[ScopedRoute, ...] = ()
    policy_version: str = "scoped-route-policy-v1"
    profile_algorithm: str = "profile-name-v1"
    runtime_source: UnknownIdentity = UnknownIdentity.UNKNOWN
    host: UnknownIdentity = UnknownIdentity.UNKNOWN
    project: UnknownIdentity = UnknownIdentity.UNKNOWN
    ownership: UnknownIdentity = UnknownIdentity.UNKNOWN
    applied: bool = False
    qualified: bool = False


_GAP = ScopedPolicyReference(status=PolicyStatus.AUTHORITY_GAP)
# service -> complete reviewed (port, legacy display label) tuple
_POLICY: tuple[tuple[str, tuple[tuple[int, str], ...]], ...] = (
    ("portainer", ((10001, "Portainer"),)),
    ("nexus", ((13081, "Nexus"), (13500, "Nexus Docker registry"), (13501, "Nexus Docker proxy registry"))),
    ("jenkins", ((11080, "Jenkins"), (11050, "Jenkins inbound agent"))),
    ("pulsar", ((14001, "Pulsar broker protocol"), (14080, "Pulsar Admin API"),
                (14081, "Pulsar Manager UI"), (7750, "Pulsar Manager backend"))),
    ("sonarqube", ((12000, "SonarQube"),)),
    ("swagger", ((16080, "Swagger UI"), (16081, "Swagger/NGINX"))),
    ("traefik", ((80, "Traefik HTTP ingress"), (443, "Traefik HTTPS ingress"))),
)
# Reviewed Classic identity and dependency semantics; caller catalogs cannot
# redefine these values or expand the supported service set.
_CATALOG_POLICY: tuple[tuple[str, str, bool, tuple[str, ...], tuple[str, ...]], ...] = (
    ("incus", "host-prerequisite", True, (), ("default", "service-access")),
    ("portainer", "managed-foundation", True, ("incus",), ("default", "service-access")),
    ("traefik", "stack", False, ("portainer",), ("default", "service-access")),
    ("nexus", "stack", False, ("portainer",), ("default", "service-access")),
    ("jenkins", "stack", False, ("portainer", "nexus"), ("default", "service-access")),
    ("pulsar", "stack", False, ("portainer",), ("default", "service-access")),
    ("sonarqube", "stack", False, ("portainer",), ("default", "service-access")),
    ("swagger", "stack", False, ("portainer",), ("default", "service-access")),
    ("infisical", "stack", False, ("portainer",), ("service-access",)),
    ("service-access", "stack", False, ("portainer", "nexus", "infisical", "traefik"), ("service-access",)),
)
_PARENT_SERVICE_IDS: tuple[tuple[str, str], ...] = (
    ("Portainer", "portainer"), ("Nexus", "nexus"), ("Jenkins", "jenkins"),
    ("Pulsar", "pulsar"), ("SonarQube", "sonarqube"), ("Swagger/NGINX", "swagger"),
    ("Traefik Ingress", "traefik"), ("Service Access", "service-access"), ("Infisical", "infisical"),
)
_ALLOWED = frozenset({"incus", "portainer", "nexus", "jenkins", "pulsar", "sonarqube",
                      "swagger", "traefik", "infisical", "service-access"})
_DEFAULT_FORBIDDEN = frozenset({"traefik", "infisical", "service-access"})
_CONFLICT = frozenset({"infisical", "service-access"})


def _listener_collision(routes: tuple[ScopedRoute, ...]) -> bool:
    for index, left in enumerate(routes):
        for right in routes[index + 1:]:
            if (left.protocol == right.protocol and left.listen_port == right.listen_port
                    and (left.listen_address == right.listen_address
                         or "0.0.0.0" in {left.listen_address, right.listen_address})):
                return True
    return False


def scoped_route_reference(manifest: object, catalog: object, *, exposure: object,
                           listen_address: object, **unsupported: object) -> ScopedPolicyReference:
    """Return only an ideal reference, or a fixed non-admitting authority gap."""
    try:
        if (unsupported or type(exposure) is not SwaggerMode or type(listen_address) is not str
                or listen_address not in {"127.0.0.1", "0.0.0.0"}):
            return _GAP
        validated = preview_migration(manifest, catalog)
        if type(catalog) is not ComponentCatalog:
            return _GAP
        checked_catalog = ComponentCatalog.model_validate(catalog.model_dump(mode="python", warnings="error"), strict=True)
        canonical = {row[0]: row[1:] for row in _CATALOG_POLICY}
        if len(canonical) != len(_CATALOG_POLICY):
            return _GAP
        for service in checked_catalog.services:
            actual = (service.kind, service.mandatory, service.dependencies, service.presets)
            if canonical.get(service.service_id) != actual:
                return _GAP
        snapshot = validated.v1_snapshot
        preset, selected, installation_id = (snapshot["service_preset"], snapshot["resolved_services"],
                                             snapshot["installation_id"])
        if (type(preset) is not str or preset not in {"default", "service-access"}
                or type(selected) is not tuple or type(installation_id) is not str
                or any(type(name) is not str or name not in _ALLOWED for name in selected)):
            return _GAP
        chosen = set(selected)
        if (not {"incus", "portainer"} <= chosen or len(chosen) != len(selected)
                or chosen & _CONFLICT or (preset == "default" and chosen & _DEFAULT_FORBIDDEN)):
            return _GAP
        if (("swagger" in chosen and exposure is not SwaggerMode.PUBLISHED)
                or ("swagger" not in chosen and exposure is not SwaggerMode.NOT_APPLICABLE)):
            return _GAP
        setup = default_setup_manifest(profile=SetupProfile.FULL, service_profile=preset,
                                       resolved_services=selected)
        if len({service for service, _ in _POLICY}) != len(_POLICY):
            return _GAP
        expected = tuple((service, port, label) for service, entries in _POLICY if service in chosen
                         for port, label in entries)
        if any(type(port) is not int or not 1 <= port <= 65535 or type(label) is not str
               for _, port, label in expected):
            return _GAP
        parent_ids = dict(_PARENT_SERVICE_IDS)
        parent_names = [group.name for group in setup.services]
        if (len(parent_names) != len(set(parent_names))
                or any(type(name) is not str or name not in parent_ids for name in parent_names)
                or {parent_ids[name] for name in parent_names} != chosen - {"incus"}):
            return _GAP
        observed = tuple((parent_ids[group.name], item.port, item.service)
                         for group in setup.services for item in group.ports)
        if any(type(port) is not int or type(label) is not str for _, port, label in observed):
            return _GAP
        if sorted(expected) != sorted(observed):
            return _GAP
        routes = tuple(sorted((ScopedRoute(service_id=service, device_name=f"tsw-proxy-{port}",
                                           protocol="tcp", listen_address=listen_address, listen_port=port,
                                           connect_address="127.0.0.1", connect_port=port, bind="host",
                                           nat=False, proxy_protocol=False)
                               for service, port, _ in expected), key=lambda item: item.listen_port))
        if (len({item.device_name for item in routes}) != len(routes)
                or _listener_collision(routes)):
            return _GAP
        profile = "tsw-profile-" + hashlib.sha256(
            b"tiny-swarm-world/incus-profile/v1\x00" + UUID(installation_id).bytes).hexdigest()[:32]
        return ScopedPolicyReference(status=PolicyStatus.REFERENCE, installation_id=installation_id,
                                     profile_name=profile, routes=routes)
    except Exception:
        return _GAP
