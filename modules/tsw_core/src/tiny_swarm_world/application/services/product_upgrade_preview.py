"""Read-only product transition preview and interrupted-checkpoint admission."""
import asyncio

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError


async def preview_product_upgrade(installation, journal, target: str, *, recovery: bool = False) -> dict[str, object]:
    checkpoint = journal.load()
    if recovery:
        if checkpoint is None or checkpoint.plan.target.product.release != target:
            raise LifecycleStateError('No matching product checkpoint; inspect the original target.')
        result = checkpoint.plan.preview()
        result['checkpoint'] = checkpoint.stage
        return result
    if checkpoint is not None and checkpoint.stage != 'completed':
        raise LifecycleStateError('Product upgrade interrupted; preview --recover before resuming.')
    if checkpoint is not None and checkpoint.plan.target.product.release == target:
        result = checkpoint.plan.preview()
        result['status'] = 'verification_required'
        return result
    plan = await asyncio.to_thread(installation.plan, target)
    return plan.preview()
