"""Private CAS profile checkpoint under installation then shared journal ownership."""
from contextlib import contextmanager
from pathlib import Path
import stat
import os
from typing import Iterator

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.lifecycle.installation_profile import InstallationLease
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ProfileLifecycleCheckpoint
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.adapters.lifecycle.update_journal import JsonUpdateJournal


class JsonProfileLifecycleJournal:
    def __init__(self, root: Path):
        self.root = root
        self.path = root / '.tiny-swarm-world/installation/profile-operation.json'
        self.component = JsonUpdateJournal(self.path.with_name('component-update.json'))
        self._lease: InstallationLease | None = None

    @contextmanager
    def exclusive(self, lease: InstallationLease) -> Iterator[None]:
        lease.require_active()
        if self._lease is not None:
            raise LifecycleStateError('Profile checkpoint already has an admitted holder.')
        from tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock import JsonInstallationOperationLock
        with JsonInstallationOperationLock(self.root).exclusive('profile-lifecycle', lease=lease), lease.journal('component'), self.component.exclusive():
            batch = self.component.load()
            if batch is not None and not batch.settled:
                raise LifecycleStateError('Settle the original component operation before profile lifecycle.')
            self._lease = lease
            try:
                yield
            finally:
                self._lease = None

    def load(self) -> ProfileLifecycleCheckpoint | None:
        try:
            raw = read_checkpoint(self.root)
            return None if raw is None else ProfileLifecycleCheckpoint.model_validate_json(raw)
        except (OSError, ValueError):
            raise LifecycleStateError('Invalid profile checkpoint; preserve state for explicit recovery.') from None

    def save(self, checkpoint: ProfileLifecycleCheckpoint, *, expected: ProfileLifecycleCheckpoint | None, lease: InstallationLease) -> None:
        if self._lease is None or self._lease is not lease:
            raise LifecycleStateError('An admitted installation/journal lease is required before profile persistence.')
        self._lease.require_active()
        try:
            checked = ProfileLifecycleCheckpoint.model_validate_json(checkpoint.model_dump_json())
            previous = self.load()
            if previous != expected:
                raise ValueError('Profile checkpoint changed.')
            if previous is not None and previous.intent != checked.intent:
                raise ValueError('Profile operation intent changed.')
            if (previous is not None and previous.installation_manifest_sha256 is not None
                    and checked.installation_manifest_sha256 != previous.installation_manifest_sha256):
                raise ValueError('Original installation manifest commitment changed.')
            expected_next = 0 if previous is None else previous.generation + 1
            if checked.generation != expected_next:
                raise ValueError('Profile checkpoint generation changed.')
            JsonManifestRepository(self.path)._replace(checked.model_dump_json(indent=2).encode() + b'\n')
        except (OSError, ValueError):
            raise LifecycleStateError('Profile checkpoint write refused or uncertain; preserve original intent.') from None


def read_checkpoint(root: Path, filename: str = 'profile-operation.json') -> bytes | None:
    from tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock import JsonInstallationOperationLock

    if filename not in {'profile-operation.json', 'profile-change.json'}:
        raise ValueError('Unsupported profile checkpoint kind.')
    try:
        directory = JsonInstallationOperationLock(root)._directory(create=False)
    except FileNotFoundError:
        return None
    try:
        try:
            descriptor = os.open(filename, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
        except FileNotFoundError:
            return None
        try:
            info = os.fstat(descriptor)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                    or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1
                    or info.st_size > 1048576):
                raise ValueError('Unsafe profile checkpoint.')
            raw = os.read(descriptor, 1048577)
            final = os.fstat(descriptor)
            fields = ('st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_nlink', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
            if len(raw) != info.st_size or any(getattr(final, key) != getattr(info, key) for key in fields):
                raise ValueError('Profile checkpoint changed while reading.')
            return raw
        finally:
            os.close(descriptor)
    finally:
        os.close(directory)
