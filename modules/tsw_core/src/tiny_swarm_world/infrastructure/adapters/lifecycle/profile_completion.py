"""Prepare only the missing final mark of an exact already-adopted creation."""
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.installation_profile import InstallationProfileService
from tiny_swarm_world.application.services.profile_completion import CreationCompletionOperation
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.node_command import AsyncLxcNodeCommandRunner
from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle import IncusProfileLifecycleRuntime
from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_journal import JsonProfileLifecycleJournal
from tiny_swarm_world.infrastructure.adapters.repositories.incus_profile_capability_repository import IncusProfileCapabilityRepository


async def prepare_creation_completion(state, consent, lease, *, recovery):
    from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_setup import clean_source_revision
    from tiny_swarm_world.infrastructure.composition_management import verify_completed_stacks

    journal = JsonProfileLifecycleJournal(state.root)
    checkpoint = journal.load()
    if not recovery or checkpoint is None or checkpoint.installation_committed:
        raise LifecycleStateError('Original creation completion requires explicit recovery.')
    lease.require_active()
    runtime = IncusProfileLifecycleRuntime(AsyncLxcNodeCommandRunner())
    if await clean_source_revision(runtime.for_preparation(lease), state.root) != checkpoint.intent.profile.controller_revision:
        raise LifecycleStateError('Original creation controller source changed.')
    service = InstallationProfileService(IncusProfileCapabilityRepository(state.root), runtime, journal,
        state.lifecycle.manifests, state.lifecycle.operation_lock)
    async def verify(manifest):
        await verify_completed_stacks(state.root, manifest, ManagedLxcBackend.INCUS,
            node_names=(checkpoint.intent.node_name, *(worker.node_name for worker in checkpoint.intent.workers)))
    operation = CreationCompletionOperation(service, checkpoint, lease, state.plan, consent, verify)
    await operation.admit_desired(state.plan)
    return operation
