from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from tiny_swarm_world.domain.node_provider.provider_model import (
    ManagedLxcBackend,
    NodeRole,
    NodeSpec,
)


_SAFE_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


class DockerSwarmLxcRiskLabel(str, Enum):
    DOCKER_IN_CONTAINER_REQUIRES_NESTING = "docker_in_container_requires_nesting"
    DOCKER_IN_CONTAINER_SYSCALL_INTERCEPTION = "docker_in_container_syscall_interception"
    DOCKER_SWARM_IN_LXC_UNVERIFIED = "docker_swarm_in_lxc_unverified"
    PROVIDER_PROFILE_MUTATION_REQUIRES_LIVE_CONSENT = (
        "provider_profile_mutation_requires_live_consent"
    )
    PRIVILEGED_PROFILE_FORBIDDEN_DEFAULT = "privileged_profile_forbidden_default"
    HOST_ACCESS_FORBIDDEN_DEFAULT = "host_access_forbidden_default"
    WSL2_LIVE_EVIDENCE_REQUIRED = "wsl2_live_evidence_required"


REQUIRED_DOCKER_SWARM_LXC_RISK_LABELS = (
    DockerSwarmLxcRiskLabel.DOCKER_IN_CONTAINER_REQUIRES_NESTING,
    DockerSwarmLxcRiskLabel.DOCKER_IN_CONTAINER_SYSCALL_INTERCEPTION,
    DockerSwarmLxcRiskLabel.DOCKER_SWARM_IN_LXC_UNVERIFIED,
    DockerSwarmLxcRiskLabel.PROVIDER_PROFILE_MUTATION_REQUIRES_LIVE_CONSENT,
    DockerSwarmLxcRiskLabel.PRIVILEGED_PROFILE_FORBIDDEN_DEFAULT,
    DockerSwarmLxcRiskLabel.HOST_ACCESS_FORBIDDEN_DEFAULT,
    DockerSwarmLxcRiskLabel.WSL2_LIVE_EVIDENCE_REQUIRED,
)


class SwarmNodeState(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    UNKNOWN = "unknown"
    ERROR = "error"


class DockerEngineState(str, Enum):
    READY = "ready"
    MISSING = "missing"
    UNKNOWN = "unknown"
    ERROR = "error"


class DockerInstallState(str, Enum):
    ALREADY_INSTALLED = "already_installed"
    INSTALLED = "installed"
    FAILED = "failed"


class SwarmManagerState(str, Enum):
    ACTIVE = "active"
    INITIALIZED = "initialized"
    PENDING = "pending"
    ERROR = "error"
    UNKNOWN = "unknown"


class WorkerJoinState(str, Enum):
    ALREADY_JOINED = "already_joined"
    JOINED = "joined"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DockerSwarmInLxcProfileContract:
    profile_name: str = "docker-swarm"
    backend_support: tuple[ManagedLxcBackend, ...] = (
        ManagedLxcBackend.INCUS,
        ManagedLxcBackend.LXD,
    )
    nesting_required: bool = True
    syscall_interception_required: bool = True
    intercept_mknod_required: bool = True
    intercept_setxattr_required: bool = True
    cgroup_policy: str = "v2_required"
    apparmor_policy: str = "provider_default"
    seccomp_policy: str = "provider_default"
    capability_additions: tuple[str, ...] = ()
    privileged_default: bool = False
    host_network: bool = False
    host_mounts: tuple[str, ...] = ()
    risk_labels: tuple[DockerSwarmLxcRiskLabel, ...] = REQUIRED_DOCKER_SWARM_LXC_RISK_LABELS

    def __post_init__(self) -> None:
        if not _SAFE_IDENTIFIER_PATTERN.fullmatch(self.profile_name):
            raise ValueError("profile name contains invalid characters")
        object.__setattr__(
            self,
            "backend_support",
            tuple(_backend(item) for item in self.backend_support),
        )
        object.__setattr__(self, "capability_additions", tuple(self.capability_additions))
        object.__setattr__(self, "host_mounts", tuple(self.host_mounts))
        object.__setattr__(
            self,
            "risk_labels",
            tuple(_risk_label(item) for item in self.risk_labels),
        )

    @classmethod
    def default_docker_swarm(cls) -> DockerSwarmInLxcProfileContract:
        return cls()

    @property
    def valid_for_node_creation(self) -> bool:
        return not self.validation_errors()

    def validation_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        if set(self.backend_support) != {ManagedLxcBackend.INCUS, ManagedLxcBackend.LXD}:
            errors.append("managed_backend_support_incomplete")
        if not self.nesting_required:
            errors.append("nesting_not_required")
        if not self.syscall_interception_required:
            errors.append("syscall_interception_not_required")
        if not self.intercept_mknod_required:
            errors.append("mknod_interception_not_required")
        if not self.intercept_setxattr_required:
            errors.append("setxattr_interception_not_required")
        if self.cgroup_policy != "v2_required":
            errors.append("cgroup_v2_not_required")
        if self.apparmor_policy != "provider_default":
            errors.append("apparmor_policy_not_provider_default")
        if self.seccomp_policy != "provider_default":
            errors.append("seccomp_policy_not_provider_default")
        if self.privileged_default:
            errors.append("privileged_default_forbidden")
        if self.host_network:
            errors.append("host_network_forbidden")
        if self.host_mounts:
            errors.append("host_mounts_forbidden")
        if self.capability_additions:
            errors.append("capability_additions_forbidden_default")
        missing_labels = set(REQUIRED_DOCKER_SWARM_LXC_RISK_LABELS) - set(self.risk_labels)
        if missing_labels:
            errors.append("risk_labels_incomplete")
        return tuple(errors)


@dataclass(frozen=True)
class ContainerDockerReadiness:
    node: NodeSpec
    observed: bool
    engine_state: DockerEngineState

    def __post_init__(self) -> None:
        object.__setattr__(self, "engine_state", _docker_engine_state(self.engine_state))

    @property
    def ready(self) -> bool:
        return not self.readiness_errors()

    def readiness_errors(self) -> tuple[str, ...]:
        if not self.observed:
            return ("docker_observed_state_missing",)
        if self.engine_state != DockerEngineState.READY:
            return (f"docker_engine_{self.engine_state.value}",)
        return ()


@dataclass(frozen=True)
class ContainerDockerInstallOutcome:
    node: NodeSpec
    state: DockerInstallState
    verified: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "state", _docker_install_state(self.state))

    @property
    def successful(self) -> bool:
        return not self.install_errors()

    def install_errors(self) -> tuple[str, ...]:
        if self.state == DockerInstallState.FAILED:
            return ("docker_install_failed",)
        if not self.verified:
            return ("docker_install_not_verified",)
        return ()


@dataclass(frozen=True)
class SwarmManagerBootstrapOutcome:
    node: NodeSpec
    state: SwarmManagerState
    manager_count: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "state", _swarm_manager_state(self.state))
        if self.manager_count is not None and self.manager_count < 0:
            raise ValueError("manager count must not be negative")

    @property
    def active(self) -> bool:
        return not self.bootstrap_errors()

    def bootstrap_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        if self.node.role != NodeRole.MANAGER:
            errors.append("manager_node_role_required")
        if self.state not in (SwarmManagerState.ACTIVE, SwarmManagerState.INITIALIZED):
            errors.append(f"swarm_manager_{self.state.value}")
        if self.manager_count is not None and self.manager_count < 1:
            errors.append("manager_quorum_missing")
        return tuple(errors)


@dataclass(frozen=True, repr=False)
class SwarmWorkerJoinCredential:
    value: str

    def __post_init__(self) -> None:
        if not self.value or self.value.isspace():
            raise ValueError("worker join credential must not be empty")

    def __repr__(self) -> str:
        return "SwarmWorkerJoinCredential(<redacted>)"

    def __str__(self) -> str:
        return "<redacted>"


@dataclass(frozen=True)
class SwarmWorkerJoinOutcome:
    node: NodeSpec
    state: WorkerJoinState
    verified: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "state", _worker_join_state(self.state))

    @property
    def joined(self) -> bool:
        return not self.join_errors()

    def join_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        if self.node.role != NodeRole.WORKER:
            errors.append("worker_node_role_required")
        if self.state not in (WorkerJoinState.ALREADY_JOINED, WorkerJoinState.JOINED):
            errors.append(f"worker_join_{self.state.value}")
        if not self.verified:
            errors.append("worker_join_not_verified")
        return tuple(errors)


@dataclass(frozen=True)
class SwarmNodeReadinessEvidence:
    node: NodeSpec
    docker_engine_observed: bool
    docker_engine_ready: bool
    swarm_state_observed: bool
    swarm_state: SwarmNodeState
    observed_role: NodeRole | None = None
    manager_count: int | None = None
    expected_node_count: int | None = None
    observed_node_count: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "swarm_state", _swarm_state(self.swarm_state))
        if self.observed_role is not None:
            object.__setattr__(self, "observed_role", _node_role(self.observed_role))
        for label, value in (
            ("manager count", self.manager_count),
            ("expected node count", self.expected_node_count),
            ("observed node count", self.observed_node_count),
        ):
            if value is not None and value < 0:
                raise ValueError(f"{label} must not be negative")

    @property
    def has_observed_state(self) -> bool:
        return self.docker_engine_observed and self.swarm_state_observed

    @property
    def ready(self) -> bool:
        return not self.readiness_errors()

    def readiness_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.has_observed_state:
            errors.append("observed_state_missing")
            return tuple(errors)
        if not self.docker_engine_ready:
            errors.append("docker_engine_not_ready")
        if self.swarm_state != SwarmNodeState.ACTIVE:
            errors.append("swarm_state_not_active")
        if self.observed_role is None:
            errors.append("node_role_missing")
        elif self.observed_role != self.node.role:
            errors.append("node_role_mismatch")
        if self.manager_count is not None and self.manager_count < 1:
            errors.append("manager_quorum_missing")
        if (
            self.expected_node_count is not None
            and self.observed_node_count is not None
            and self.observed_node_count < self.expected_node_count
        ):
            errors.append("swarm_node_count_incomplete")
        return tuple(errors)


def _backend(value: ManagedLxcBackend | str) -> ManagedLxcBackend:
    return value if isinstance(value, ManagedLxcBackend) else ManagedLxcBackend(str(value))


def _risk_label(value: DockerSwarmLxcRiskLabel | str) -> DockerSwarmLxcRiskLabel:
    return value if isinstance(value, DockerSwarmLxcRiskLabel) else DockerSwarmLxcRiskLabel(str(value))


def _swarm_state(value: SwarmNodeState | str) -> SwarmNodeState:
    return value if isinstance(value, SwarmNodeState) else SwarmNodeState(str(value))


def _docker_engine_state(value: DockerEngineState | str) -> DockerEngineState:
    return value if isinstance(value, DockerEngineState) else DockerEngineState(str(value))


def _docker_install_state(value: DockerInstallState | str) -> DockerInstallState:
    return value if isinstance(value, DockerInstallState) else DockerInstallState(str(value))


def _swarm_manager_state(value: SwarmManagerState | str) -> SwarmManagerState:
    return value if isinstance(value, SwarmManagerState) else SwarmManagerState(str(value))


def _worker_join_state(value: WorkerJoinState | str) -> WorkerJoinState:
    return value if isinstance(value, WorkerJoinState) else WorkerJoinState(str(value))


def _node_role(value: NodeRole | str) -> NodeRole:
    return value if isinstance(value, NodeRole) else NodeRole(str(value))
