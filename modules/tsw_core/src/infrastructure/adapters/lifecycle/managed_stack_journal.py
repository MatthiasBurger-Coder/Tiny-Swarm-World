"""Owner-private atomic management intent, serialized by the installation lease."""
import os
from pathlib import Path
import stat
import tempfile

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.lifecycle.installation_profile import InstallationLease
from tiny_swarm_world.domain.lifecycle.managed_stack import ManagedStackIntent


class JsonManagedStackJournal:
    def __init__(self, path: Path, lease: InstallationLease):
        self.path, self.lease = path, lease

    def _parent(self):
        self.lease.require_active()
        if self.path.parent.is_symlink():
            raise LifecycleStateError('Unsafe managed journal directory.')
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = self.path.parent.stat()
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
            raise LifecycleStateError('Managed journal requires an owner-private directory.')

    def load(self) -> ManagedStackIntent | None:
        self._parent()
        try:
            descriptor = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:
            return None
        except OSError:
            raise LifecycleStateError('Managed journal unavailable.') from None
        with os.fdopen(descriptor, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                    or stat.S_IMODE(info.st_mode) != 0o600 or info.st_size > 65536):
                raise LifecycleStateError('Managed journal is unsafe or oversized.')
            try:
                return ManagedStackIntent.model_validate_json(stream.read(65537))
            except ValueError:
                raise LifecycleStateError('Managed journal invalid; preserve for recovery.') from None

    def save(self, value: ManagedStackIntent) -> None:
        self._parent()
        validated = ManagedStackIntent.model_validate_json(value.model_dump_json())
        previous = self.load()
        reversing = (previous is not None and value.recovery_of == previous.target_fingerprint
                     and value.recovery_source == previous.source and previous.source is not None
                     and value.source is not None and value.source.model_copy(update={
                         'definition_fingerprint': previous.source.definition_fingerprint}) == previous.source
                     and value.source.definition_fingerprint in {previous.source.definition_fingerprint, previous.target_fingerprint})
        if previous is not None and previous.phase != 'verified' and not reversing and (
                previous.installation_id != value.installation_id or previous.operation_id != value.operation_id
                or previous.stack_name != value.stack_name or previous.target_fingerprint != value.target_fingerprint):
            raise LifecycleStateError('Managed journal intent cannot be replaced while unsettled.')
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.path.parent, prefix='.managed-stack-', delete=False) as stream:
                temporary = Path(stream.name)
                os.fchmod(stream.fileno(), 0o600)
                stream.write(validated.model_dump_json().encode())
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            descriptor = os.open(self.path.parent, os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        except OSError:
            raise LifecycleStateError('Managed journal durability uncertain; preserve operation state.') from None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
