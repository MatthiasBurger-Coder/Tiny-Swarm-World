"""Opaque operation ownership; application services know no filesystem locks."""
from contextlib import AbstractContextManager, contextmanager
from typing import Iterator, Protocol

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError


class InstallationLease(Protocol):
    operation_id: str
    def require_active(self) -> None: ...
    def journal(self, kind: str) -> AbstractContextManager[None]: ...


class InstallationOperationLock(Protocol):
    def exclusive(self, operation: str, *, lease: InstallationLease | None = None) -> AbstractContextManager[InstallationLease]: ...


@contextmanager
def installation_operation(lock: InstallationOperationLock | None, operation: str,
                           lease: InstallationLease | None = None) -> Iterator[InstallationLease]:
    if lock is None:
        raise LifecycleStateError('An installation operation lock is required before mutation.')
    with lock.exclusive(operation, lease=lease) as admitted:
        admitted.require_active()
        yield admitted


def require_legacy_runtime_policy(manifest) -> None:
    from tiny_swarm_world.domain.lifecycle.models import legacy_runtime_compatible

    if not legacy_runtime_compatible(manifest):
        raise LifecycleStateError('Installation policy requires the separately admitted scoped-profile/exposure/ownership capability; no legacy runtime mutation is allowed.')


from dataclasses import dataclass
from typing import Literal
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import (
    ManagerCreateIntent, ProfileCapabilityMatrix, ProfileLifecycleCheckpoint,
)


@dataclass(frozen=True)
class WorkerObservation:
    node_name: str
    state: Literal['absent', 'stopped', 'running', 'foreign']
    instance_uuid: str | None
    no_proxy: bool


@dataclass(frozen=True)
class ProfileObservation:
    """Validated adapter observations, never an untrusted caller JSON assertion."""
    client_version: str
    server_version: str
    preservation_sha256: str
    base_profiles_sha256: str
    profile_state: Literal['absent', 'exact', 'foreign']
    instance_state: Literal['absent', 'stopped', 'running', 'foreign']
    effective_routes_match: bool
    forbidden_listener: bool
    listeners_match: bool
    listeners_clear: bool
    observation_sha256: str
    instance_uuid: str | None
    workers: tuple[WorkerObservation, ...] = ()


class ProfileCapabilityRepository(Protocol):
    def load(self) -> ProfileCapabilityMatrix: ...


class ProfileLifecycleRuntime(Protocol):
    def for_operation(self, lease: InstallationLease, intent: ManagerCreateIntent) -> "ProfileLifecycleRuntime": ...
    async def inspect(self, intent: ManagerCreateIntent) -> ProfileObservation: ...
    async def create_profile(self, intent: ManagerCreateIntent) -> None: ...
    async def update_profile(self, intent: ManagerCreateIntent, before: ManagerCreateIntent) -> None: ...
    async def init_instance(self, intent: ManagerCreateIntent) -> None: ...
    async def start_instance(self, intent: ManagerCreateIntent) -> None: ...
    async def delete_instance(self, intent: ManagerCreateIntent) -> None: ...
    async def delete_profile(self, intent: ManagerCreateIntent) -> None: ...
    async def init_worker(self, intent: ManagerCreateIntent, node_name: str) -> None: ...
    async def start_worker(self, intent: ManagerCreateIntent, node_name: str) -> None: ...


class ProfileLifecycleJournal(Protocol):
    def exclusive(self, lease: InstallationLease) -> AbstractContextManager[None]: ...
    def load(self) -> ProfileLifecycleCheckpoint | None: ...
    def save(self, checkpoint: ProfileLifecycleCheckpoint, *, expected: ProfileLifecycleCheckpoint | None, lease: InstallationLease) -> None: ...


from tiny_swarm_world.domain.lifecycle.selection import SelectionPlan
from tiny_swarm_world.domain.lifecycle.models import PortainerOwnership


class ProfileSetupOperation(Protocol):
    intent: ManagerCreateIntent
    lease: InstallationLease
    @property
    def verified_stack_ownership(self) -> dict[str, PortainerOwnership]: ...
    async def admit_desired(self, plan: SelectionPlan) -> None: ...
    async def ensure_manager(self) -> None: ...
    async def ensure_worker(self, node_name: str) -> None: ...
    async def verify_node(self, node_name: str) -> None: ...
    async def verify_effective_routes(self) -> None: ...
    async def commit_installation(self) -> None: ...
    async def record_stack_ownership(self, service_id: str, ownership: PortainerOwnership) -> None: ...


class ProfileVerificationObserver(Protocol):
    """Read-only proof consumer; exposes no lease, admission or mutation method."""
    async def verify_node(self, node_name: str) -> None: ...
    async def verify_effective_routes(self) -> None: ...
