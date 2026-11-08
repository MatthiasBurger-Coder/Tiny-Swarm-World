"""Private atomic journal with nonblocking exclusive batch ownership."""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import tempfile

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.update_execution import UpdateBatch


class JsonUpdateJournal:
    def __init__(self, path: Path, *, gateway: bool = False, product: bool = False):
        self.path = path
        self.gateway = gateway
        self.product = product

    @contextmanager
    def exclusive(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            descriptor = os.open(self.path.with_suffix('.lock'), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            with os.fdopen(descriptor, 'a') as stream:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                if not self.gateway:
                    from tiny_swarm_world.infrastructure.adapters.lifecycle.portainer_journal import JsonPortainerJournal

                    checkpoint = JsonPortainerJournal(self.path.with_name('portainer-upgrade.json')).load()
                    if checkpoint is not None and not checkpoint.settled:
                        raise LifecycleStateError('Recover the interrupted Portainer operation before component updates.')
                if not self.product:
                    from tiny_swarm_world.infrastructure.adapters.lifecycle.product_journal import JsonProductJournal

                    product = JsonProductJournal(self.path.with_name('product-upgrade.json')).load()
                    if product is not None and product.stage != 'completed':
                        raise LifecycleStateError('Resume the interrupted product upgrade before component/gateway updates.')
                yield
        except OSError:
            raise LifecycleStateError('Update journal unavailable or another update is active; inspect before retrying.') from None

    def load(self) -> UpdateBatch | None:
        try:
            if self.path.is_symlink():
                raise ValueError
            if not self.path.exists():
                return None
            return UpdateBatch.model_validate_json(self.path.read_bytes())
        except (OSError, ValueError):
            raise LifecycleStateError('Invalid or unavailable update journal; preserve it for recovery.') from None

    def save(self, batch: UpdateBatch) -> None:
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.path.parent, prefix='.component-update-', delete=False) as stream:
                temporary = Path(stream.name)
                os.fchmod(stream.fileno(), 0o600)
                stream.write(batch.model_dump_json(indent=2).encode() + b'\n')
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            directory = os.open(self.path.parent, os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except OSError:
            raise LifecycleStateError('Update journal durability uncertain; inspect state and resume before setup.') from None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
