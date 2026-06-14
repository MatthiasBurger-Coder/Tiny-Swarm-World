from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from types import MappingProxyType
from typing import Mapping


class NodeProviderKind(str, Enum):
    LXC_NATIVE = "lxc_native"
    UNSUPPORTED = "unsupported"


class ManagedLxcBackend(str, Enum):
    INCUS = "incus"
    LXD = "lxd"


class ManagedLxcBackendSelectionStatus(str, Enum):
    SELECTED = "selected"
    AMBIGUOUS = "ambiguous"
    MISSING = "missing"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class ManagedLxcBackendSelection:
    status: ManagedLxcBackendSelectionStatus
    backend: ManagedLxcBackend | None = None
    candidates: tuple[ManagedLxcBackend, ...] = ()
    remediation: tuple[str, ...] = ()
    evidence: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        candidates = tuple(self.candidates)
        remediation = tuple(self.remediation)
        _validate_backend_selection(self.status, self.backend, candidates)
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "remediation", remediation)
        object.__setattr__(self, "evidence", sanitized_evidence(self.evidence))

    @classmethod
    def for_backend(
        cls,
        backend: ManagedLxcBackend,
        *,
        remediation: tuple[str, ...] = (),
        evidence: Mapping[str, str] | None = None,
    ) -> ManagedLxcBackendSelection:
        return cls(
            status=ManagedLxcBackendSelectionStatus.SELECTED,
            backend=backend,
            candidates=(backend,),
            remediation=remediation,
            evidence={} if evidence is None else evidence,
        )

    @classmethod
    def ambiguous(
        cls,
        *,
        candidates: tuple[ManagedLxcBackend, ...],
        remediation: tuple[str, ...] = (),
        evidence: Mapping[str, str] | None = None,
    ) -> ManagedLxcBackendSelection:
        return cls(
            status=ManagedLxcBackendSelectionStatus.AMBIGUOUS,
            candidates=candidates,
            remediation=remediation,
            evidence={} if evidence is None else evidence,
        )

    @classmethod
    def missing(
        cls,
        *,
        remediation: tuple[str, ...] = (),
        evidence: Mapping[str, str] | None = None,
    ) -> ManagedLxcBackendSelection:
        return cls(
            status=ManagedLxcBackendSelectionStatus.MISSING,
            remediation=remediation,
            evidence={} if evidence is None else evidence,
        )

    @classmethod
    def unsupported(
        cls,
        *,
        remediation: tuple[str, ...] = (),
        evidence: Mapping[str, str] | None = None,
    ) -> ManagedLxcBackendSelection:
        return cls(
            status=ManagedLxcBackendSelectionStatus.UNSUPPORTED,
            remediation=remediation,
            evidence={} if evidence is None else evidence,
        )

    @property
    def selected(self) -> bool:
        return self.status == ManagedLxcBackendSelectionStatus.SELECTED

    @property
    def blocks_mutation(self) -> bool:
        return not self.selected

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "backend": None if self.backend is None else self.backend.value,
            "candidates": [candidate.value for candidate in self.candidates],
            "selected": self.selected,
            "blocks_mutation": self.blocks_mutation,
            "remediation": list(self.remediation),
            "evidence": dict(self.evidence),
        }


class ProviderReadinessStatus(str, Enum):
    READY = "ready"
    BACKEND_MISSING = "backend_missing"
    BACKEND_AMBIGUOUS = "backend_ambiguous"
    BACKEND_UNSUPPORTED = "backend_unsupported"
    EXECUTABLE_MISSING = "executable_missing"
    DAEMON_UNAVAILABLE = "daemon_unavailable"
    HOST_UNSUPPORTED = "host_unsupported"
    SYSTEMD_UNAVAILABLE = "systemd_unavailable"
    WSL_UNSUPPORTED = "wsl_unsupported"
    PROFILE_MISSING = "profile_missing"
    PERMISSION_DENIED = "permission_denied"
    TIMEOUT = "timeout"
    UNSUPPORTED = "unsupported"
    UNKNOWN_FAILURE = "unknown_failure"


@dataclass(frozen=True)
class ProviderReadiness:
    provider: NodeProviderKind
    status: ProviderReadinessStatus
    backend_selection: ManagedLxcBackendSelection | None = None
    remediation: tuple[str, ...] = ()
    evidence: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        remediation = tuple(self.remediation)
        _validate_provider_readiness(
            self.provider,
            self.status,
            self.backend_selection,
        )
        object.__setattr__(self, "remediation", remediation)
        object.__setattr__(self, "evidence", sanitized_evidence(self.evidence))

    @property
    def ready(self) -> bool:
        return self.status == ProviderReadinessStatus.READY

    @property
    def blocks_mutation(self) -> bool:
        return not self.ready

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": self.provider.value,
            "status": self.status.value,
            "ready": self.ready,
            "blocks_mutation": self.blocks_mutation,
            "backend_selection": None
            if self.backend_selection is None
            else self.backend_selection.to_dict(),
            "remediation": list(self.remediation),
            "evidence": dict(self.evidence),
        }


class ProviderSelectionStatus(str, Enum):
    SELECTED = "selected"
    BLOCKED = "blocked"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class ProviderSelection:
    requested_provider: NodeProviderKind
    selected_provider: NodeProviderKind
    status: ProviderSelectionStatus
    backend_selection: ManagedLxcBackendSelection | None = None
    remediation: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        remediation = tuple(self.remediation)
        _validate_provider_selection(
            self.requested_provider,
            self.selected_provider,
            self.status,
            self.backend_selection,
        )
        object.__setattr__(self, "remediation", remediation)

    @classmethod
    def from_lxc_backend_selection(
        cls,
        backend_selection: ManagedLxcBackendSelection,
    ) -> ProviderSelection:
        status = (
            ProviderSelectionStatus.SELECTED
            if backend_selection.selected
            else ProviderSelectionStatus.BLOCKED
        )
        return cls(
            requested_provider=NodeProviderKind.LXC_NATIVE,
            selected_provider=NodeProviderKind.LXC_NATIVE,
            status=status,
            backend_selection=backend_selection,
            remediation=backend_selection.remediation,
        )

    @property
    def selected(self) -> bool:
        return self.status == ProviderSelectionStatus.SELECTED

    @property
    def blocks_mutation(self) -> bool:
        return not self.selected

    def to_dict(self) -> dict[str, object]:
        return {
            "requested_provider": self.requested_provider.value,
            "selected_provider": self.selected_provider.value,
            "status": self.status.value,
            "selected": self.selected,
            "blocks_mutation": self.blocks_mutation,
            "backend_selection": None
            if self.backend_selection is None
            else self.backend_selection.to_dict(),
            "remediation": list(self.remediation),
        }


class NodeRole(str, Enum):
    MANAGER = "manager"
    WORKER = "worker"


@dataclass(frozen=True)
class NodeSpec:
    name: str
    role: NodeRole
    provider: NodeProviderKind
    backend: ManagedLxcBackend | None = None

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", self.name):
            raise ValueError("node name must be lowercase DNS-label compatible")
        if self.provider == NodeProviderKind.UNSUPPORTED:
            raise ValueError("unsupported provider cannot be a desired node provider")
        if self.provider != NodeProviderKind.LXC_NATIVE and self.backend is not None:
            raise ValueError("managed LXC backend is valid only for lxc_native nodes")

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "role": self.role.value,
            "provider": self.provider.value,
            "backend": None if self.backend is None else self.backend.value,
        }


def _validate_backend_selection(
    status: ManagedLxcBackendSelectionStatus,
    backend: ManagedLxcBackend | None,
    candidates: tuple[ManagedLxcBackend, ...],
) -> None:
    if status == ManagedLxcBackendSelectionStatus.SELECTED:
        if backend is None:
            raise ValueError("selected managed LXC backend requires a backend")
        if candidates and backend not in candidates:
            raise ValueError("selected managed LXC backend candidates must include backend")
        return
    if backend is not None:
        raise ValueError("blocked managed LXC backend selection must not set backend")
    if status == ManagedLxcBackendSelectionStatus.AMBIGUOUS and len(candidates) < 2:
        raise ValueError("ambiguous managed LXC backend selection requires candidates")


def _validate_provider_readiness(
    provider: NodeProviderKind,
    status: ProviderReadinessStatus,
    backend_selection: ManagedLxcBackendSelection | None,
) -> None:
    if provider == NodeProviderKind.LXC_NATIVE:
        if backend_selection is None:
            raise ValueError("lxc_native readiness requires managed backend selection")
        if status == ProviderReadinessStatus.READY and not backend_selection.selected:
            raise ValueError("ready lxc_native provider requires selected backend")
        required_backend_status = {
            ProviderReadinessStatus.BACKEND_MISSING: ManagedLxcBackendSelectionStatus.MISSING,
            ProviderReadinessStatus.BACKEND_AMBIGUOUS: ManagedLxcBackendSelectionStatus.AMBIGUOUS,
            ProviderReadinessStatus.BACKEND_UNSUPPORTED: ManagedLxcBackendSelectionStatus.UNSUPPORTED,
        }.get(status)
        if required_backend_status is not None and backend_selection.status != required_backend_status:
            raise ValueError("provider readiness status contradicts backend selection")
        return
    if backend_selection is not None:
        raise ValueError("managed LXC backend selection is valid only for lxc_native")
    if provider == NodeProviderKind.UNSUPPORTED and status == ProviderReadinessStatus.READY:
        raise ValueError("unsupported provider cannot be ready")


def _validate_provider_selection(
    requested_provider: NodeProviderKind,
    selected_provider: NodeProviderKind,
    status: ProviderSelectionStatus,
    backend_selection: ManagedLxcBackendSelection | None,
) -> None:
    if selected_provider != requested_provider:
        raise ValueError("provider selection must not change the requested provider")
    if requested_provider == NodeProviderKind.LXC_NATIVE:
        if backend_selection is None:
            raise ValueError("lxc_native selection requires managed backend selection")
        if status == ProviderSelectionStatus.SELECTED and not backend_selection.selected:
            raise ValueError("selected lxc_native provider requires selected backend")
        if status != ProviderSelectionStatus.SELECTED and backend_selection.selected:
            raise ValueError("selected backend cannot be paired with blocked selection")
    elif backend_selection is not None:
        raise ValueError("managed LXC backend selection is valid only for lxc_native")
    if status == ProviderSelectionStatus.SELECTED and selected_provider == NodeProviderKind.UNSUPPORTED:
        raise ValueError("unsupported provider cannot be selected")


UNSAFE_EVIDENCE_KEY_PARTS = (
    "command",
    "environment",
    "gateway",
    "host_ip",
    "ip_address",
    "local_path",
    "password",
    "path",
    "raw",
    "secret",
    "stderr",
    "stdout",
    "token",
    "user",
    "username",
    "vm_ip",
)

_IPV4_PATTERN = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_IPV6_PATTERN = re.compile(r"\b(?:[0-9a-fA-F]{0,4}:){2,}[0-9a-fA-F]{0,4}\b")
_ABSOLUTE_PATH_PATTERN = re.compile(r"(^|[\s=:])(?:/[\w.-]+){2,}")
_WINDOWS_PATH_PATTERN = re.compile(r"\b[A-Za-z]:\\")
_COMMAND_PATTERN = re.compile(
    r"\b(?:bash|curl|docker|docker-compose|incus|iptables|lxc|lxd|"
    r"netplan|netsh|python3?|sh|socat|sudo|wsl)\s+\S+",
    re.IGNORECASE,
)
_SCRIPT_PATH_PATTERN = re.compile(r"\b\S+\.(?:py|sh|ps1|bat)\b")
_SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"\b(?:api[_-]?key|passphrase|password|secret|token)\s*[:=]",
    re.IGNORECASE,
)
_URL_USERINFO_PATTERN = re.compile(r"\b[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@")


def sanitized_evidence(evidence: Mapping[str, str]) -> Mapping[str, str]:
    for key, value in evidence.items():
        normalized_key = str(key).lower()
        normalized_value = str(value)
        if any(part in normalized_key for part in UNSAFE_EVIDENCE_KEY_PARTS):
            raise ValueError("evidence contains unsafe keys")
        if _contains_unsafe_evidence_value(normalized_value):
            raise ValueError("evidence contains unsafe values")
    return MappingProxyType(dict(evidence))


def _contains_unsafe_evidence_value(value: str) -> bool:
    return any(
        pattern.search(value)
        for pattern in (
            _IPV4_PATTERN,
            _IPV6_PATTERN,
            _ABSOLUTE_PATH_PATTERN,
            _WINDOWS_PATH_PATTERN,
            _COMMAND_PATTERN,
            _SCRIPT_PATH_PATTERN,
            _SECRET_ASSIGNMENT_PATTERN,
            _URL_USERINFO_PATTERN,
        )
    ) or "\n" in value or "\r" in value
