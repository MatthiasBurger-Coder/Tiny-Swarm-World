"""Atomic private product progress using the shared component execution lock."""
from contextlib import contextmanager

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.domain.lifecycle.product_upgrade import ProductCheckpoint
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.adapters.lifecycle.update_journal import JsonUpdateJournal


class JsonProductJournal:
    def __init__(self, path, *, source_binder=None):
        self.path = path
        self.lock = JsonUpdateJournal(path.with_name('component-update.json'), product=True)
        self.source_binder = source_binder

    @contextmanager
    def exclusive(self):
        with self.lock.exclusive():
            batch = self.lock.load()
            if batch is not None and not batch.settled:
                raise LifecycleStateError('Settle the component update before upgrading the product.')
            yield

    def load(self):
        try:
            if self.path.is_symlink():
                raise ValueError
            if not self.path.exists():
                return None
            return ProductCheckpoint.model_validate_json(self.path.read_bytes())
        except (OSError, ValueError):
            raise LifecycleStateError('Invalid product checkpoint; preserve it and inspect the original operation.') from None

    def save(self, checkpoint):
        ProductCheckpoint.model_validate_json(checkpoint.model_dump_json())
        if checkpoint.stage == 'admitted' and checkpoint.plan.configuration_source is not None:
            if self.source_binder is None:
                raise LifecycleStateError('Bound product configuration requires its explicit persistence adapter.')
            self.source_binder(checkpoint.plan)
        JsonManifestRepository(self.path)._replace(checkpoint.model_dump_json(indent=2).encode() + b'\n')
