from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from tiny_swarm_world.domain.inventory.safe_text import validate_observed_inventory_text
from tiny_swarm_world.domain.inventory.verification import VerificationResult


@dataclass(frozen=True)
class VmObservedState:
    name: str
    status: str = "unknown"
    role: str = ""
    ip_addresses: tuple[str, ...] = field(default_factory=tuple)
    verification: VerificationResult = field(
        default_factory=lambda: VerificationResult("vm", message="VM state not checked.")
    )

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("observed VM name must not be empty")
        _validate_observed_field("name", self.name)
        _validate_observed_field("status", self.status)
        _validate_observed_field("role", self.role)
        object.__setattr__(self, "ip_addresses", _safe_string_tuple("ip_addresses", self.ip_addresses))

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status,
            "role": self.role,
            "ip_addresses": list(self.ip_addresses),
            "verification": self.verification.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "VmObservedState":
        return cls(
            name=str(data.get("name", "")),
            status=str(data.get("status", "unknown")),
            role=str(data.get("role", "")),
            ip_addresses=_string_sequence(data.get("ip_addresses", ())),
            verification=_verification_from_mapping(data.get("verification"), "vm"),
        )


@dataclass(frozen=True)
class NetworkObservedState:
    name: str
    status: str = "unknown"
    addresses: tuple[str, ...] = field(default_factory=tuple)
    verification: VerificationResult = field(
        default_factory=lambda: VerificationResult("network", message="Network state not checked.")
    )

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("observed network name must not be empty")
        _validate_observed_field("name", self.name)
        _validate_observed_field("status", self.status)
        object.__setattr__(self, "addresses", _safe_string_tuple("addresses", self.addresses))

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status,
            "addresses": list(self.addresses),
            "verification": self.verification.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "NetworkObservedState":
        return cls(
            name=str(data.get("name", "")),
            status=str(data.get("status", "unknown")),
            addresses=_string_sequence(data.get("addresses", ())),
            verification=_verification_from_mapping(data.get("verification"), "network"),
        )


@dataclass(frozen=True)
class DockerObservedState:
    installed: bool = False
    version: str = ""
    status: str = "unknown"
    verification: VerificationResult = field(
        default_factory=lambda: VerificationResult("docker", message="Docker state not checked.")
    )

    def __post_init__(self) -> None:
        _validate_observed_field("version", self.version)
        _validate_observed_field("status", self.status)

    def to_dict(self) -> dict[str, object]:
        return {
            "installed": self.installed,
            "version": self.version,
            "status": self.status,
            "verification": self.verification.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "DockerObservedState":
        return cls(
            installed=bool(data.get("installed", False)),
            version=str(data.get("version", "")),
            status=str(data.get("status", "unknown")),
            verification=_verification_from_mapping(data.get("verification"), "docker"),
        )


@dataclass(frozen=True)
class SwarmObservedState:
    active: bool = False
    node_count: int = 0
    manager_count: int = 0
    status: str = "unknown"
    verification: VerificationResult = field(
        default_factory=lambda: VerificationResult("swarm", message="Swarm state not checked.")
    )

    def __post_init__(self) -> None:
        _validate_observed_field("status", self.status)

    def to_dict(self) -> dict[str, object]:
        return {
            "active": self.active,
            "node_count": self.node_count,
            "manager_count": self.manager_count,
            "status": self.status,
            "verification": self.verification.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "SwarmObservedState":
        return cls(
            active=bool(data.get("active", False)),
            node_count=_int_value(data.get("node_count", 0)),
            manager_count=_int_value(data.get("manager_count", 0)),
            status=str(data.get("status", "unknown")),
            verification=_verification_from_mapping(data.get("verification"), "swarm"),
        )


@dataclass(frozen=True)
class StackObservedState:
    name: str
    status: str = "unknown"
    services: tuple[str, ...] = field(default_factory=tuple)
    verification: VerificationResult = field(
        default_factory=lambda: VerificationResult("stack", message="Stack state not checked.")
    )

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("observed stack name must not be empty")
        _validate_observed_field("name", self.name)
        _validate_observed_field("status", self.status)
        object.__setattr__(self, "services", _safe_string_tuple("services", self.services))

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status,
            "services": list(self.services),
            "verification": self.verification.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "StackObservedState":
        return cls(
            name=str(data.get("name", "")),
            status=str(data.get("status", "unknown")),
            services=_string_sequence(data.get("services", ())),
            verification=_verification_from_mapping(data.get("verification"), "stack"),
        )


@dataclass(frozen=True)
class ArtifactRegistryObservedState:
    name: str
    endpoint: str = ""
    status: str = "unknown"
    verification: VerificationResult = field(
        default_factory=lambda: VerificationResult(
            "artifact-registry",
            message="Artifact registry state not checked.",
        )
    )

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("observed artifact registry name must not be empty")
        _validate_observed_field("name", self.name)
        _validate_observed_field("endpoint", self.endpoint)
        _validate_observed_field("status", self.status)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "endpoint": self.endpoint,
            "status": self.status,
            "verification": self.verification.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "ArtifactRegistryObservedState":
        return cls(
            name=str(data.get("name", "")),
            endpoint=str(data.get("endpoint", "")),
            status=str(data.get("status", "unknown")),
            verification=_verification_from_mapping(
                data.get("verification"),
                "artifact-registry",
            ),
        )


@dataclass(frozen=True)
class ObservedInventory:
    vms: tuple[VmObservedState, ...] = field(default_factory=tuple)
    networks: tuple[NetworkObservedState, ...] = field(default_factory=tuple)
    docker: DockerObservedState = field(default_factory=DockerObservedState)
    swarm: SwarmObservedState = field(default_factory=SwarmObservedState)
    stacks: tuple[StackObservedState, ...] = field(default_factory=tuple)
    artifact_registries: tuple[ArtifactRegistryObservedState, ...] = field(
        default_factory=tuple
    )
    verification_results: tuple[VerificationResult, ...] = field(default_factory=tuple)
    schema_version: str = "1"

    def __post_init__(self) -> None:
        if self.schema_version != "1":
            raise ValueError("unsupported observed inventory schema version")
        object.__setattr__(self, "vms", tuple(self.vms))
        object.__setattr__(self, "networks", tuple(self.networks))
        object.__setattr__(self, "stacks", tuple(self.stacks))
        object.__setattr__(self, "artifact_registries", tuple(self.artifact_registries))
        object.__setattr__(self, "verification_results", tuple(self.verification_results))

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "vms": [vm.to_dict() for vm in self.vms],
            "networks": [network.to_dict() for network in self.networks],
            "docker": self.docker.to_dict(),
            "swarm": self.swarm.to_dict(),
            "stacks": [stack.to_dict() for stack in self.stacks],
            "artifact_registries": [
                registry.to_dict() for registry in self.artifact_registries
            ],
            "verification_results": [
                verification.to_dict() for verification in self.verification_results
            ],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "ObservedInventory":
        return cls(
            schema_version=str(data.get("schema_version", "1")),
            vms=tuple(VmObservedState.from_dict(vm) for vm in _mapping_sequence(data.get("vms", ()))),
            networks=tuple(
                NetworkObservedState.from_dict(network)
                for network in _mapping_sequence(data.get("networks", ()))
            ),
            docker=DockerObservedState.from_dict(_mapping_value(data.get("docker", {}))),
            swarm=SwarmObservedState.from_dict(_mapping_value(data.get("swarm", {}))),
            stacks=tuple(
                StackObservedState.from_dict(stack)
                for stack in _mapping_sequence(data.get("stacks", ()))
            ),
            artifact_registries=tuple(
                ArtifactRegistryObservedState.from_dict(registry)
                for registry in _mapping_sequence(data.get("artifact_registries", ()))
            ),
            verification_results=tuple(
                VerificationResult.from_dict(result)
                for result in _mapping_sequence(data.get("verification_results", ()))
            ),
        )


def _verification_from_mapping(value: object, target_id: str) -> VerificationResult:
    if value is None:
        return VerificationResult(target_id, message="State not checked.")
    return VerificationResult.from_dict(_mapping_value(value))


def _string_tuple(values: Sequence[object]) -> tuple[str, ...]:
    if isinstance(values, str):
        raise ValueError("inventory collection fields must not be strings")
    return tuple(str(value) for value in values)


def _safe_string_tuple(field_name: str, values: Sequence[object]) -> tuple[str, ...]:
    return tuple(
        validate_observed_inventory_text(field_name, value)
        for value in _string_tuple(values)
    )


def _validate_observed_field(field_name: str, value: object) -> None:
    validate_observed_inventory_text(field_name, str(value))


def _object_sequence(value: object) -> tuple[object, ...]:
    if value is None:
        return ()
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ValueError("inventory collection fields must be sequences")
    return tuple(value)


def _string_sequence(value: object) -> tuple[str, ...]:
    return tuple(str(item) for item in _object_sequence(value))


def _mapping_sequence(value: object) -> tuple[Mapping[str, object], ...]:
    items = _object_sequence(value)
    if not all(isinstance(item, Mapping) for item in items):
        raise ValueError("inventory state entries must be mappings")
    return tuple(item for item in items if isinstance(item, Mapping))


def _mapping_value(value: object) -> Mapping[str, object]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError("inventory state entries must be mappings")
    return value


def _int_value(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise ValueError("integer inventory fields must be integers or strings")
