"""Descriptor-bound owner-private lock for all writers of one anchor installation."""
from contextlib import contextmanager
from collections.abc import Callable
import fcntl
import os
from pathlib import Path
import stat
from uuid import uuid4
from threading import Lock
from typing import Any, Iterator

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.lifecycle.installation_profile import InstallationLease, require_legacy_runtime_policy
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.project_filesystem import ProjectFilesystemKind
from tiny_swarm_world.infrastructure.adapters.host.project_filesystem_inspector import ProjectFilesystemInspector


_ERROR = 'Installation operation ownership is unsafe, unavailable or already held; preserve state and retry after inspection.'


def _identity(info: os.stat_result) -> tuple[int, int]:
    return info.st_dev, info.st_ino


def _private(info: os.stat_result, directory: bool) -> None:
    expected = 0o700 if directory else 0o600
    kind = stat.S_ISDIR if directory else stat.S_ISREG
    if not kind(info.st_mode) or info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != expected or (not directory and info.st_nlink != 1):
        raise OSError('unsafe operation state')


class _Lease:
    def __init__(self, authority: 'JsonInstallationOperationLock', directory: int, descriptor: int):
        self.authority = authority
        self.directory = directory
        self.descriptor = descriptor
        self.pid = os.getpid()
        self.operation_id = uuid4().hex
        self.active = True
        self.holder: str | None = None
        self.guard = Lock()

    def require_active(self) -> None:
        try:
            if not self.active or os.getpid() != self.pid:
                raise OSError('inactive lease')
            _private(os.fstat(self.directory), True)
            observed = os.fstat(self.descriptor)
            _private(observed, False)
            if _identity(observed) != _identity(os.stat('operation.lock', dir_fd=self.directory, follow_symlinks=False)):
                raise OSError('replaced operation lock')
            current = self.authority._directory(create=False)
            try:
                if _identity(os.fstat(current)) != _identity(os.fstat(self.directory)):
                    raise OSError('replaced operation directory')
            finally:
                os.close(current)
        except (OSError, ValueError):
            raise LifecycleStateError(_ERROR) from None

    @contextmanager
    def journal(self, kind: str) -> Iterator[None]:
        with self.guard:
            self.require_active()
            if kind not in {'component', 'product'} or self.holder is not None:
                raise LifecycleStateError('Only one journal may be held under an installation operation.')
            self.holder = kind
        try:
            yield
        finally:
            with self.guard:
                self.holder = None


class JsonInstallationOperationLock:
    def __init__(self, root: Path):
        expanded = root.expanduser()
        if not expanded.is_absolute() or '..' in expanded.parts:
            raise LifecycleStateError(_ERROR)
        self.root = expanded
        self.path = expanded / '.tiny-swarm-world' / 'installation' / 'operation.lock'

    def _directory(self, *, create: bool) -> int:
        # Use mountinfo classification even on native Linux: no external command,
        # and an unknown/Windows mount cannot become a private lock authority.
        inspection = ProjectFilesystemInspector().inspect(str(self.root), HostEnvironmentKind.WSL2)
        if inspection.kind is not ProjectFilesystemKind.WSL_LINUX:
            raise OSError('unsupported operation filesystem')
        fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
        try:
            for index, part in enumerate((*self.root.parts[1:], '.tiny-swarm-world', 'installation')):
                private = index >= len(self.root.parts) - 1
                try:
                    child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                except FileNotFoundError:
                    if not create or not private:
                        raise
                    os.mkdir(part, 0o700, dir_fd=fd)
                    os.fsync(fd)
                    child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = child
                info = os.fstat(fd)
                if private:
                    _private(info, True)
                elif (info.st_uid not in {0, os.geteuid()}
                      or info.st_mode & 0o022 and not (info.st_uid == 0 and info.st_mode & stat.S_ISVTX)):
                    raise OSError('unsafe operation ancestor')
            result, fd = fd, -1
            return result
        finally:
            if fd >= 0:
                os.close(fd)

    @contextmanager
    def exclusive(self, operation: str, *, lease: InstallationLease | None = None) -> Iterator[InstallationLease]:
        if operation not in {'adoption', 'selection', 'setup', 'add', 'component-update', 'portainer-upgrade',
                             'product-upgrade', 'recovery', 'cleanup', 'platform', 'deployment', 'classic-update'}:
            raise LifecycleStateError('Unsupported installation operation.')
        if lease is not None:
            if not isinstance(lease, _Lease) or lease.authority.root != self.root:
                raise LifecycleStateError(_ERROR)
            lease.require_active()
            yield lease
            return
        directory = descriptor = -1
        admitted: _Lease | None = None
        try:
            directory = self._directory(create=True)
            descriptor = os.open('operation.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=directory)
            _private(os.fstat(descriptor), False)
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            os.fsync(descriptor)
            os.fsync(directory)
            admitted = _Lease(self, directory, descriptor)
            admitted.require_active()
            yield admitted
        except OSError:
            raise LifecycleStateError(_ERROR) from None
        finally:
            if admitted is not None:
                admitted.active = False
            if descriptor >= 0:
                os.close(descriptor)
            if directory >= 0:
                os.close(directory)


class InstallationLockedWorkflow:
    """Decorate an existing mutation workflow without introducing an executor."""
    def __init__(self, workflow: Any, lock: JsonInstallationOperationLock, operation: str,
                 lease: InstallationLease | None = None, *, expected_token: str | None = None,
                 workflow_factory: Callable[[InstallationLease], Any] | None = None):
        self.workflow, self.lock, self.operation, self.lease = workflow, lock, operation, lease
        self.expected_token, self.workflow_factory = expected_token, workflow_factory

    def __getattr__(self, name: str) -> Any:
        return getattr(self.workflow, name)

    async def run(self, *args: Any, **kwargs: Any) -> Any:
        from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository

        with self.lock.exclusive(self.operation, lease=self.lease) as admitted:
            current = JsonManifestRepository(self.lock.root / '.tiny-swarm-world' / 'installation' / 'manifest.json').load()
            if current.manifest is not None:
                require_legacy_runtime_policy(current.manifest)
            if self.lease is None:
                if current.token != self.expected_token:
                    raise LifecycleStateError('Installation changed since workflow construction; compose the operation again.')
            workflow = self.workflow if self.workflow_factory is None else self.workflow_factory(admitted)
            return await workflow.run(*args, **kwargs)


def locked_workflows(group: Any, root: Path, operation: str, lease: InstallationLease | None = None) -> Any:
    """Wrap only declared mutating workflow fields; verification stays read-only."""
    from dataclasses import fields, replace
    from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository

    lock = JsonInstallationOperationLock(root)
    repository = JsonManifestRepository(root / '.tiny-swarm-world' / 'installation' / 'manifest.json')
    token = repository.load().token
    changes = {}
    for field in fields(group):
        value = getattr(group, field.name)
        if field.name == 'cluster':
            changes[field.name] = locked_workflows(value, root, operation, lease)
        elif field.name in {'init', 'reconcile', 'expose', 'reset', 'destroy', 'repair_lxc_proxy_drift',
                            'docker', 'swarm_bootstrap', 'bootstrap', 'apply', 'run'}:
            changes[field.name] = InstallationLockedWorkflow(value, lock, operation, lease,
                                                             expected_token=token)
    return replace(group, **changes)


def bind_operation_lease(group: Any, lease: InstallationLease | None) -> Any:
    """Return a private delegation view; never publish authority on shared objects."""
    from copy import copy
    from dataclasses import fields, is_dataclass, replace

    if lease is not None:
        lease.require_active()
    if isinstance(group, InstallationLockedWorkflow):
        return InstallationLockedWorkflow(
            group.workflow, group.lock, group.operation, lease,
            expected_token=group.expected_token, workflow_factory=group.workflow_factory,
        )
    if is_dataclass(group) and not isinstance(group, type):
        changes = {
            field.name: bind_operation_lease(getattr(group, field.name), lease)
            for field in fields(group)
            if field.name in {'workflows', 'lifecycle', 'cluster', 'init', 'reconcile', 'expose', 'reset', 'destroy',
                              'repair_lxc_proxy_drift', 'docker', 'swarm_bootstrap', 'bootstrap', 'apply', 'run'}
        }
        return replace(group, **changes)
    from tiny_swarm_world.application.services.platform.lifecycle import PlatformLifecycleOrchestrator
    if isinstance(group, PlatformLifecycleOrchestrator):
        lifecycle_view = copy(group)
        lifecycle_view.workflows = bind_operation_lease(group.workflows, lease)
        return lifecycle_view
    # Classic's public entrypoint also keeps an unbound copy. Only the private
    # caller view receives the explicit capability, never the original service.
    if hasattr(group, 'operation_lease'):
        private = copy(group)
        private.operation_lease = lease
        return private
    return group


def locked_services(services: Any, root: Path, operation: str) -> Any:
    from dataclasses import replace

    return replace(services, workflows=locked_workflows(services.workflows, root, operation))


def locked_setup_services(services: Any, root: Path,
                          factory: Callable[[InstallationLease], Any],
                          lease: InstallationLease | None = None) -> Any:
    from dataclasses import replace

    workflows = locked_workflows(services.workflows, root, 'setup', lease)
    workflows.run.workflow_factory = lambda active: factory(active).workflows.run
    return replace(services, workflows=workflows)


def require_anchor_runtime_policy(root: Path) -> None:
    from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository

    snapshot = JsonManifestRepository(root / '.tiny-swarm-world' / 'installation' / 'manifest.json').load()
    if snapshot.manifest is not None:
        require_legacy_runtime_policy(snapshot.manifest)
