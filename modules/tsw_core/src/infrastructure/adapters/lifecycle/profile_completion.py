"""Prepare only the missing final mark of an exact already-adopted creation."""
from pathlib import Path

from tiny_swarm_world.application.ports.installation import CommittedGuidedInstallation
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.installation_profile import InstallationProfileService
from tiny_swarm_world.application.services.profile_completion import CreationCompletionOperation
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.node_command import AsyncLxcNodeCommandRunner
from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.lifecycle import IncusProfileLifecycleRuntime
from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_journal import JsonProfileLifecycleJournal
from tiny_swarm_world.infrastructure.adapters.repositories.incus_profile_capability_repository import IncusProfileCapabilityRepository


async def verify_guided_completion(root: Path, expected: CommittedGuidedInstallation, password: str) -> None:
    """Reobserve the exact committed creation without admitting a runtime writer."""
    from tiny_swarm_world.infrastructure.adapters.installation.guided_observation import committed_installation
    from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_change import JsonProfileChangeJournal
    from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_observation import ScopedProfileObserver
    from tiny_swarm_world.infrastructure.composition_lifecycle import build_installation_lifecycle_service
    from tiny_swarm_world.infrastructure.composition_management import verify_completed_stacks

    lifecycle = build_installation_lifecycle_service(root)
    journal = JsonProfileLifecycleJournal(root)
    changes = JsonProfileChangeJournal(root)
    snapshot = lifecycle.manifests.load()
    checkpoint = journal.load()
    manifest = snapshot.manifest
    if (checkpoint is None or manifest is None or changes.load() is not None
            or committed_installation(snapshot, checkpoint) != expected):
        raise LifecycleStateError('Original guided completion changed before runtime verification.')
    lifecycle.catalog.load().validate_manifest(manifest)
    intent = checkpoint.intent
    observed = await ScopedProfileObserver(root, lifecycle).observe(expected_revision=intent.profile.controller_revision)
    if observed != intent:
        raise LifecycleStateError('Original guided runtime does not match its committed scope.')
    await verify_completed_stacks(root, manifest, ManagedLxcBackend.INCUS, operator_password=password,
        node_names=(intent.node_name, *(worker.node_name for worker in intent.workers)))
    if lifecycle.manifests.load() != snapshot or journal.load() != checkpoint or changes.load() is not None:
        raise LifecycleStateError('Original guided completion changed during runtime verification.')


async def prepare_creation_completion(state, consent, lease, *, recovery):
    from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_setup import clean_source_revision
    from tiny_swarm_world.infrastructure.composition_management import verify_completed_stacks

    journal = JsonProfileLifecycleJournal(state.root)
    checkpoint = journal.load()
    if not recovery or checkpoint is None or checkpoint.installation_committed:
        raise LifecycleStateError('Original creation completion requires explicit recovery.')
    lease.require_active()
    capabilities = IncusProfileCapabilityRepository(state.root)
    runtime = IncusProfileLifecycleRuntime(AsyncLxcNodeCommandRunner(), capabilities=capabilities)
    if await clean_source_revision(runtime.for_preparation(lease), state.root) != checkpoint.intent.profile.controller_revision:
        raise LifecycleStateError('Original creation controller source changed.')
    service = InstallationProfileService(capabilities, runtime, journal,
        state.lifecycle.manifests, state.lifecycle.operation_lock)
    async def verify(manifest):
        await verify_completed_stacks(state.root, manifest, ManagedLxcBackend.INCUS,
            node_names=(checkpoint.intent.node_name, *(worker.node_name for worker in checkpoint.intent.workers)))
    operation = CreationCompletionOperation(service, checkpoint, lease, state.plan, consent, verify)
    await operation.admit_desired(state.plan)
    return operation
