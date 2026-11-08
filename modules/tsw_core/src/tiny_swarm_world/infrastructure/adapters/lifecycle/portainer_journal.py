"""Use the same atomic state and exclusive lock policy as component updates."""
from contextlib import contextmanager

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.portainer_upgrade import PortainerCheckpoint
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.adapters.lifecycle.update_journal import JsonUpdateJournal


class JsonPortainerJournal:
    def __init__(self, path):
        self.path = path
        # Share the component execution lock: gateway and stack updates cannot race.
        self.lock = JsonUpdateJournal(path.with_name('component-update.json'), gateway=True)

    @contextmanager
    def exclusive(self):
        with self.lock.exclusive():
            batch = self.lock.load()
            if batch is not None and not batch.settled:
                raise LifecycleStateError('Complete/recover the component batch before upgrading Portainer.')
            yield

    def load(self) -> PortainerCheckpoint | None:
        try:
            if self.path.is_symlink():
                raise ValueError
            if not self.path.exists():
                return None
            return PortainerCheckpoint.model_validate_json(self.path.read_bytes())
        except (OSError, ValueError):
            raise LifecycleStateError('Portainer checkpoint invalid; preserve state and inspect recovery metadata.') from None

    def save(self, checkpoint: PortainerCheckpoint) -> None:
        PortainerCheckpoint.model_validate_json(checkpoint.model_dump_json())
        JsonManifestRepository(self.path)._replace(checkpoint.model_dump_json(indent=2).encode() + b'\n')
