"""Explicit scoped operation admission never replaces a legacy guard with a flag."""
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.lifecycle.installation_profile import require_legacy_runtime_policy
from tiny_swarm_world.domain.lifecycle.models import legacy_runtime_compatible


async def admit_runtime_policy(manifest, lease, kind, consent, factory):
    if legacy_runtime_compatible(manifest):
        require_legacy_runtime_policy(manifest)
        return None
    if factory is None:
        raise LifecycleStateError('Scoped policy requires observed installation-profile runtime admission.')
    operation = await factory(manifest, lease, kind, consent)
    lease.require_active()
    operation.intent.profile.validate_manifest(manifest)
    await operation.verify_effective_routes()
    return operation


async def recheck_runtime_policy(operation):
    if operation is not None:
        operation.lease.require_active()
        await operation.verify_effective_routes()
