from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum

from tiny_swarm_world.domain.inventory.safe_text import validate_observed_inventory_text
from tiny_swarm_world.domain.inventory.verification import VerificationResult

_LOCAL_TOPOLOGY_PATTERNS = (
    re.compile(r"\b(?:127|10)\.(?:\d{1,3}\.){2}\d{1,3}\b"),
    re.compile(r"\b172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}\b"),
    re.compile(r"\b192\.168\.\d{1,3}\.\d{1,3}\b"),
    re.compile(r"(^|[\s=:])(?:/home/|/mnt/|/root/|/tmp/|/var/|[A-Za-z]:[\\/])"),
)


class IngressDiscoveryCategory(str, Enum):
    GIT = "git"
    DOCKER = "docker"
    SWARM = "swarm"
    LXC = "lxc"
    NETWORK = "network"
    ROUTE = "route"
    CERTIFICATE = "certificate"
    TRAEFIK = "traefik"


@dataclass(frozen=True)
class IngressDiscoveryFinding:
    category: IngressDiscoveryCategory
    name: str
    status: str = "unknown"
    summary: str = ""
    verification: VerificationResult = field(
        default_factory=lambda: VerificationResult(
            "ingress:discovery",
            message="Ingress discovery not checked.",
        )
    )

    def __post_init__(self) -> None:
        category = IngressDiscoveryCategory(self.category)
        if not self.name:
            raise ValueError("ingress discovery finding name must not be empty")
        _validate_discovery_field("name", self.name)
        _validate_discovery_field("status", self.status)
        _validate_discovery_field("summary", self.summary)
        object.__setattr__(self, "category", category)

    def to_dict(self) -> dict[str, object]:
        return {
            "category": self.category.value,
            "name": self.name,
            "status": self.status,
            "summary": self.summary,
            "verification": self.verification.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "IngressDiscoveryFinding":
        return cls(
            category=IngressDiscoveryCategory(str(data.get("category", ""))),
            name=str(data.get("name", "")),
            status=str(data.get("status", "unknown")),
            summary=str(data.get("summary", "")),
            verification=_verification_from_mapping(data.get("verification")),
        )


@dataclass(frozen=True)
class IngressDiscoverySnapshot:
    findings: tuple[IngressDiscoveryFinding, ...] = field(default_factory=tuple)
    verification_results: tuple[VerificationResult, ...] = field(default_factory=tuple)
    schema_version: str = "1"

    def __post_init__(self) -> None:
        if self.schema_version != "1":
            raise ValueError("unsupported ingress discovery schema version")
        object.__setattr__(self, "findings", tuple(self.findings))
        object.__setattr__(self, "verification_results", tuple(self.verification_results))

    def by_category(
        self,
        category: IngressDiscoveryCategory | str,
    ) -> tuple[IngressDiscoveryFinding, ...]:
        selected = IngressDiscoveryCategory(category)
        return tuple(finding for finding in self.findings if finding.category == selected)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "findings": [finding.to_dict() for finding in self.findings],
            "verification_results": [
                verification.to_dict() for verification in self.verification_results
            ],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "IngressDiscoverySnapshot":
        return cls(
            schema_version=str(data.get("schema_version", "1")),
            findings=tuple(
                IngressDiscoveryFinding.from_dict(finding)
                for finding in _mapping_sequence(data.get("findings", ()))
            ),
            verification_results=tuple(
                VerificationResult.from_dict(result)
                for result in _mapping_sequence(data.get("verification_results", ()))
            ),
        )


def _verification_from_mapping(value: object) -> VerificationResult:
    if value is None:
        return VerificationResult(
            "ingress:discovery",
            message="Ingress discovery not checked.",
        )
    return VerificationResult.from_dict(_mapping_value(value))


def _validate_discovery_field(field_name: str, value: object) -> None:
    validate_ingress_summary_text(field_name, str(value))


def validate_ingress_summary_text(field_name: str, value: str) -> None:
    text = validate_observed_inventory_text(field_name, value)
    if any(pattern.search(text) for pattern in _LOCAL_TOPOLOGY_PATTERNS):
        raise ValueError(
            f"local topology details are not allowed in ingress discovery: {field_name}"
        )


def _object_sequence(value: object) -> tuple[object, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValueError("ingress discovery collection fields must be sequences")
    return tuple(value)


def _mapping_sequence(value: object) -> tuple[Mapping[str, object], ...]:
    items = _object_sequence(value)
    if not all(isinstance(item, Mapping) for item in items):
        raise ValueError("ingress discovery entries must be mappings")
    return tuple(item for item in items if isinstance(item, Mapping))


def _mapping_value(value: object) -> Mapping[str, object]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError("ingress discovery entries must be mappings")
    return value
