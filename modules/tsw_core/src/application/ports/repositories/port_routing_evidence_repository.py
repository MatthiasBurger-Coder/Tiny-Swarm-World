from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RoutingEvidenceCredential:
    username_label: str
    item_reference: str

    def to_dict(self) -> dict[str, str]:
        return {
            "item_reference": self.item_reference,
            "username_label": self.username_label,
        }


@dataclass(frozen=True)
class RoutingEvidenceRoute:
    service_name: str
    hostname: str
    upstream_service: str
    upstream_port: int
    profile_member: bool
    health_check_url: str
    service_access_url: str
    credential: RoutingEvidenceCredential | None = None

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "health_check_url": self.health_check_url,
            "hostname": self.hostname,
            "profile_member": self.profile_member,
            "service_access_url": self.service_access_url,
            "service_name": self.service_name,
            "upstream_port": self.upstream_port,
            "upstream_service": self.upstream_service,
        }
        if self.credential is not None:
            result["credential"] = self.credential.to_dict()
        return result


@dataclass(frozen=True)
class RoutingEvidenceFallbackPort:
    port_id: str
    service: str
    port: int
    classification: str

    def to_dict(self) -> dict[str, object]:
        return {
            "classification": self.classification,
            "port": self.port,
            "port_id": self.port_id,
            "service": self.service,
        }


@dataclass(frozen=True)
class RoutingEvidenceHealthTarget:
    service: str
    target: str
    upstream_service: str
    upstream_port: int

    def to_dict(self) -> dict[str, object]:
        return {
            "service": self.service,
            "target": self.target,
            "upstream_port": self.upstream_port,
            "upstream_service": self.upstream_service,
        }


@dataclass(frozen=True)
class RoutingEvidenceServiceAccessLink:
    service: str
    url: str
    preferred: bool = True
    credential: RoutingEvidenceCredential | None = None

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "preferred": self.preferred,
            "service": self.service,
            "url": self.url,
        }
        if self.credential is not None:
            result["credential"] = self.credential.to_dict()
        return result


@dataclass(frozen=True)
class RoutingEvidenceSkippedRoute:
    service: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"reason": self.reason, "service": self.service}


@dataclass(frozen=True)
class EffectiveAccessModelEvidence:
    evidence_kind: str
    generated_at: str
    service_profile: str
    public_ports: tuple[int, ...]
    gateway_public_ingress_ports: tuple[int, ...]
    diagnostic_fallback_ports: tuple[RoutingEvidenceFallbackPort, ...]
    service_access_preferred_url_source: str
    routes: tuple[RoutingEvidenceRoute, ...]
    health_check_targets: tuple[RoutingEvidenceHealthTarget, ...]
    service_access_links: tuple[RoutingEvidenceServiceAccessLink, ...]
    skipped_routes: tuple[RoutingEvidenceSkippedRoute, ...]
    result: str

    def to_dict(self) -> dict[str, object]:
        return {
            "diagnostic_fallback_ports": [
                fallback.to_dict() for fallback in self.diagnostic_fallback_ports
            ],
            "evidence_kind": self.evidence_kind,
            "gateway_public_ingress_ports": list(self.gateway_public_ingress_ports),
            "generated_at": self.generated_at,
            "health_check_targets": [target.to_dict() for target in self.health_check_targets],
            "public_ports": list(self.public_ports),
            "result": self.result,
            "routes": [route.to_dict() for route in self.routes],
            "service_access_links": [link.to_dict() for link in self.service_access_links],
            "service_access_preferred_url_source": self.service_access_preferred_url_source,
            "service_profile": self.service_profile,
            "skipped_routes": [route.to_dict() for route in self.skipped_routes],
        }


class PortRoutingEvidenceRepository(ABC):
    @abstractmethod
    def write_effective_access_model(self, evidence: EffectiveAccessModelEvidence) -> None:
        """Atomically replace the local effective-access-model evidence."""
