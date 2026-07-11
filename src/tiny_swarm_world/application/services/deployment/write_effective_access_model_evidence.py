from __future__ import annotations

import re
from collections.abc import Callable
from datetime import UTC, datetime
from urllib.parse import urlsplit

from tiny_swarm_world.application.ports.repositories.port_effective_access_model_repository import (
    PortEffectiveAccessModelRepository,
)
from tiny_swarm_world.application.ports.repositories.port_routing_evidence_repository import (
    EffectiveAccessModelEvidence,
    PortRoutingEvidenceRepository,
    RoutingEvidenceCredential,
    RoutingEvidenceFallbackPort,
    RoutingEvidenceHealthTarget,
    RoutingEvidenceRoute,
    RoutingEvidenceServiceAccessLink,
    RoutingEvidenceSkippedRoute,
)
from tiny_swarm_world.domain.deployment import ServiceStackProfile
from tiny_swarm_world.domain.ingress import (
    CredentialReference,
    DesiredHttpsIngress,
    DesiredHttpsRoute,
)


EFFECTIVE_ACCESS_MODEL_EVIDENCE_KIND = "effective_access_model"
EFFECTIVE_ACCESS_MODEL_EVIDENCE_RESULT = "generated"
EFFECTIVE_ACCESS_MODEL_EVIDENCE_TARGET_ID = (
    "deployment:effective-access-model-evidence"
)
_CREDENTIAL_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@ -]{0,63}$")
_INFISICAL_ITEM_REFERENCE_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9_.-]*(?:/[A-Za-z0-9][A-Za-z0-9_.-]*)+$"
)


class WriteEffectiveAccessModelEvidence:
    """Project the effective access model into a fixed redacted evidence contract."""

    deployment_target_id = EFFECTIVE_ACCESS_MODEL_EVIDENCE_TARGET_ID

    def __init__(
        self,
        effective_access_model_repository: PortEffectiveAccessModelRepository,
        routing_evidence_repository: PortRoutingEvidenceRepository,
        service_profile: ServiceStackProfile | str,
        *,
        clock: Callable[[], datetime] | None = None,
    ):
        self.effective_access_model_repository = effective_access_model_repository
        self.routing_evidence_repository = routing_evidence_repository
        self.service_profile = ServiceStackProfile(service_profile)
        self.clock = clock or _utc_now

    def run(self) -> EffectiveAccessModelEvidence:
        evidence = build_effective_access_model_evidence(
            self.effective_access_model_repository.get_effective_access_model(),
            service_profile=self.service_profile,
            generated_at=_utc_timestamp(self.clock()),
        )
        self.routing_evidence_repository.write_effective_access_model(evidence)
        return evidence


def build_effective_access_model_evidence(
    access_model: DesiredHttpsIngress,
    *,
    service_profile: ServiceStackProfile | str,
    generated_at: str,
) -> EffectiveAccessModelEvidence:
    routes = tuple(
        sorted(
            (_route_projection(route) for route in access_model.routes),
            key=lambda route: (
                route.service_name,
                route.hostname,
                route.upstream_service,
                route.upstream_port,
            ),
        )
    )
    fallback_ports = tuple(
        sorted(
            (
                RoutingEvidenceFallbackPort(
                    port_id=fallback.port_id,
                    service=fallback.service_name,
                    port=fallback.port,
                    classification=fallback.classification,
                )
                for fallback in access_model.diagnostic_fallback_ports
            ),
            key=lambda fallback: (
                fallback.service,
                fallback.port_id,
                fallback.port,
                fallback.classification,
            ),
        )
    )
    health_targets = tuple(
        sorted(
            (
                RoutingEvidenceHealthTarget(
                    service=route.service_name,
                    target=route.health_check_url,
                    upstream_service=route.upstream_service,
                    upstream_port=route.upstream_port,
                )
                for route in routes
            ),
            key=lambda target: (
                target.service,
                target.target,
                target.upstream_service,
                target.upstream_port,
            ),
        )
    )
    service_access_links = tuple(
        sorted(
            (
                RoutingEvidenceServiceAccessLink(
                    service=route.service_name,
                    url=route.service_access_url,
                    credential=route.credential,
                )
                for route in routes
            ),
            key=lambda link: (link.service, link.url),
        )
    )
    skipped_routes = tuple(
        sorted(
            (
                RoutingEvidenceSkippedRoute(
                    service=skipped.service_name,
                    reason=skipped.reason,
                )
                for skipped in access_model.skipped_routes
            ),
            key=lambda skipped: (skipped.service, skipped.reason),
        )
    )
    public_ports = tuple(sorted(access_model.public_ports))
    return EffectiveAccessModelEvidence(
        evidence_kind=EFFECTIVE_ACCESS_MODEL_EVIDENCE_KIND,
        generated_at=generated_at,
        service_profile=ServiceStackProfile(service_profile).value,
        public_ports=public_ports,
        gateway_public_ingress_ports=public_ports,
        diagnostic_fallback_ports=fallback_ports,
        service_access_preferred_url_source=(
            access_model.service_access_preferred_url_source
        ),
        routes=routes,
        health_check_targets=health_targets,
        service_access_links=service_access_links,
        skipped_routes=skipped_routes,
        result=EFFECTIVE_ACCESS_MODEL_EVIDENCE_RESULT,
    )


def _route_projection(route: DesiredHttpsRoute) -> RoutingEvidenceRoute:
    base_url = f"https://{route.hostname}"
    health_check_url = _safe_route_url(
        route.health_check_url or base_url,
        expected_hostname=route.hostname,
    )
    service_access_url = _safe_route_url(
        route.service_access_url or base_url,
        expected_hostname=route.hostname,
    )
    return RoutingEvidenceRoute(
        service_name=route.service_name,
        hostname=route.hostname,
        upstream_service=route.upstream_service,
        upstream_port=route.upstream_port,
        profile_member=route.profile_member,
        health_check_url=health_check_url,
        service_access_url=service_access_url,
        credential=_credential_projection(route.credential),
    )


def _credential_projection(
    credential: CredentialReference | None,
) -> RoutingEvidenceCredential | None:
    if credential is None:
        return None
    if not _CREDENTIAL_LABEL_PATTERN.fullmatch(credential.username_label):
        raise ValueError("routing evidence credential label is not a safe label")
    if not _INFISICAL_ITEM_REFERENCE_PATTERN.fullmatch(credential.item_reference):
        raise ValueError("routing evidence credential item reference is invalid")
    return RoutingEvidenceCredential(
        username_label=credential.username_label,
        item_reference=credential.item_reference,
    )


def _safe_route_url(value: str, *, expected_hostname: str) -> str:
    parsed = urlsplit(value)
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("routing evidence URL contains an invalid port") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname != expected_hostname
        or parsed.username is not None
        or parsed.password is not None
        or port is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("routing evidence URL is not a safe routed HTTPS URL")
    return value


def _utc_timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("routing evidence clock must return a timezone-aware value")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _utc_now() -> datetime:
    return datetime.now(UTC)
