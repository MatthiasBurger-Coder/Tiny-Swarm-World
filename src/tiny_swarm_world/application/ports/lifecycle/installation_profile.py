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
