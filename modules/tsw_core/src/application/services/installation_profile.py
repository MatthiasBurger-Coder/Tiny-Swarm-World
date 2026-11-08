"""Checkpoint-bound scoped profile lifecycle; every effect requires readback."""
import asyncio
from copy import copy
from collections.abc import Awaitable, Callable

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError, ManifestRepository
from tiny_swarm_world.application.ports.lifecycle.installation_profile import (
    InstallationLease, InstallationOperationLock, ProfileCapabilityRepository,
    ProfileLifecycleJournal, ProfileLifecycleRuntime, installation_operation,
)
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ManagerCreateIntent, ProfileCapabilityMatrix, ProfileLifecycleCheckpoint
from tiny_swarm_world.domain.preflight import LiveConsent


class InstallationProfileService:
    def __init__(self, capabilities: ProfileCapabilityRepository, runtime: ProfileLifecycleRuntime,
                 journal: ProfileLifecycleJournal, manifests: ManifestRepository,
                 operation_lock: InstallationOperationLock):
        self.capabilities, self.runtime, self.journal = capabilities, runtime, journal
        self.manifests, self.operation_lock = manifests, operation_lock

    async def run(self, intent: ManagerCreateIntent, *, consent: LiveConsent,
                  lease: InstallationLease | None = None, recovery: bool = False) -> ProfileLifecycleCheckpoint:
        matrix = admitted_matrix(self.capabilities, consent)
        checked = ManagerCreateIntent.model_validate_json(intent.model_dump_json())
        operation = 'profile-recovery' if recovery else 'profile-lifecycle'
        with installation_operation(self.operation_lock, operation, lease) as active, self.journal.exclusive(active):
            execution = copy(self)
            execution.runtime = self.runtime.for_operation(active, checked)
            checkpoint = await admit(execution, checked, matrix, active, recovery)
            return await advance(execution, checkpoint, matrix, active)

    async def cleanup(self, intent: ManagerCreateIntent, *, consent: LiveConsent,
                      lease: InstallationLease | None = None) -> ProfileLifecycleCheckpoint:
        matrix = admitted_matrix(self.capabilities, consent)
        with installation_operation(self.operation_lock, 'profile-cleanup', lease) as active, self.journal.exclusive(active):
            execution = copy(self)
            execution.runtime = self.runtime.for_operation(active, intent)
            checkpoint = require_checkpoint(execution, intent)
            return await retained_cleanup(execution, checkpoint, matrix, active)

    async def commit_installation(self, intent: ManagerCreateIntent, *, consent: LiveConsent,
                                  lease: InstallationLease) -> ProfileLifecycleCheckpoint:
        matrix = admitted_matrix(self.capabilities, consent)
        with self.journal.exclusive(lease):
            execution = copy(self)
            execution.runtime = self.runtime.for_operation(lease, intent)
            checkpoint = require_checkpoint(execution, intent)
            observation = await observe_checkpoint(execution, checkpoint, matrix)
            require_running(observation)
            from tiny_swarm_world.application.services.profile_setup import require_workers_running
            require_workers_running(checkpoint, observation)
            manifest = self.manifests.load().manifest
            if (checkpoint.stage != 'completed' or manifest is None or manifest.schema_version != 2
                    or manifest.installation_id != intent.profile.installation_id
                    or manifest.installation_profile != intent.profile.profile
                    or manifest.checkpoint_reference != 'profile-' + intent.profile.operation_id
                    or not committed_stack_policy(checkpoint, manifest)):
                raise LifecycleStateError('Installation completion is not bound to the original profile checkpoint.')
            from tiny_swarm_world.domain.lifecycle.profile_lifecycle import installation_manifest_sha256
            if (checkpoint.installation_manifest_sha256 is not None
                    and installation_manifest_sha256(manifest) != checkpoint.installation_manifest_sha256):
                raise LifecycleStateError('Original installation manifest commitment changed.')
            if checkpoint.installation_committed:
                return checkpoint
            return record(self, checkpoint, lease, installation_committed=True)


def admitted_matrix(repository: ProfileCapabilityRepository, consent: LiveConsent) -> ProfileCapabilityMatrix:
    if not consent.accepted:
        raise LifecycleStateError('Explicit live consent is required before scoped profile lifecycle.')
    matrix = ProfileCapabilityMatrix.model_validate_json(repository.load().model_dump_json())
    if not matrix.admitted_versions:
        raise LifecycleStateError('No Incus version is admitted for scoped profile lifecycle; no mutation is allowed.')
    return matrix


def require_checkpoint(service, intent):
    checkpoint = service.journal.load()
    if checkpoint is None or checkpoint.intent != intent:
        raise LifecycleStateError('Recovery requires the exact original scoped profile intent.')
    return checkpoint


async def observe(service, intent, matrix):
    result = await service.runtime.inspect(intent)
    if (not matrix.admits(result.client_version, result.server_version)
            or result.client_version != intent.profile.incus_version
            or result.server_version != intent.profile.incus_version):
        raise LifecycleStateError('Exact Incus client/server capability admission changed.')
    if (result.preservation_sha256 != intent.preservation_sha256
            or result.base_profiles_sha256 != intent.base_profiles_sha256
            or result.profile_state == 'foreign' or result.instance_state == 'foreign'
            or result.forbidden_listener
            or {worker.node_name for worker in result.workers} != {worker.node_name for worker in intent.workers}
            or any(worker.state == 'foreign' or not worker.no_proxy for worker in result.workers)):
        raise LifecycleStateError('Profile, consumer, instance, listener or preservation ownership is unknown or changed.')
    return result


async def admit(service, intent, matrix, lease, recovery):
    previous = service.journal.load()
    if previous is not None:
        if previous.intent != intent:
            raise LifecycleStateError('Another profile operation owns the retained checkpoint.')
        if previous.stage == 'cleaned' and recovery:
            observed = await observe(service, intent, matrix)
            if (observed.profile_state != 'absent' or observed.instance_state != 'absent'
                    or not observed.listeners_clear or any(worker.state != 'absent' for worker in observed.workers)):
                raise LifecycleStateError('Cleaned targets reappeared; retain the original operation.')
            return record(service, previous, lease, stage='intent', previous_stage='intent',
                observation_sha256=observed.observation_sha256, instance_uuid=None, worker_uuids={},
                pending_action=None, pending_node=None)
        same_setup_phase = (previous.stage not in {'recoverable', 'cleaned'} and previous.pending_action is None
                            and lease.operation_id == intent.profile.operation_id)
        if not recovery and not previous.settled and not same_setup_phase:
            raise LifecycleStateError('Resume the exact original profile checkpoint explicitly.')
        return previous
    if recovery:
        raise LifecycleStateError('No original profile checkpoint is available for recovery.')
    observed = await observe(service, intent, matrix)
    if (observed.profile_state != 'absent' or observed.instance_state != 'absent' or not observed.listeners_clear
            or any(worker.state != 'absent' for worker in observed.workers)):
        raise LifecycleStateError('Fresh scoped creation requires proven absent targets and an empty listener baseline.')
    checkpoint = ProfileLifecycleCheckpoint(intent=intent, observation_sha256=observed.observation_sha256)
    service.journal.save(checkpoint, expected=None, lease=lease)
    return checkpoint


def record(service, checkpoint, lease, **changes):
    payload = checkpoint.model_dump()
    payload.update(changes, generation=checkpoint.generation + 1)
    updated = ProfileLifecycleCheckpoint.model_validate(payload)
    service.journal.save(updated, expected=checkpoint, lease=lease)
    return updated


def stage(service, checkpoint, lease, name, observed):
    return record(service, checkpoint, lease, stage=name, previous_stage=name,
                  observation_sha256=observed.observation_sha256, pending_action=None, pending_node=None,
                  instance_uuid=observed.instance_uuid or checkpoint.instance_uuid)


def require_stopped(observed):
    if (observed.profile_state != 'exact' or observed.instance_state != 'stopped'
            or not observed.effective_routes_match or not observed.listeners_clear):
        raise LifecycleStateError('Stopped manager ownership and complete effective routes are not proven.')


def require_running(observed):
    if (observed.profile_state != 'exact' or observed.instance_state != 'running'
            or not observed.effective_routes_match or not observed.listeners_match):
        raise LifecycleStateError('Running manager ownership and complete effective listeners are not proven.')


async def write_and_observe(service, checkpoint, matrix, lease, before, action,
                            effect: Callable[[ManagerCreateIntent], Awaitable[None]]):
    checkpoint = record(service, checkpoint, lease, pending_action=action, observation_sha256=before.observation_sha256)
    fresh = await observe_checkpoint(service, checkpoint, matrix)
    if fresh.observation_sha256 != checkpoint.observation_sha256:
        raise LifecycleStateError('Profile precondition changed after durable mutation intent.')
    # A failed/lost command is uncertain. Never retry it here; only a fresh,
    # complete readback may establish its exact already-applied postcondition.
    try:
        await settle_effect(effect(checkpoint.intent))
    except (OSError, ValueError, RuntimeError, TimeoutError):
        pass
    return checkpoint, await observe(service, checkpoint.intent, matrix)


async def advance(service, checkpoint, matrix, lease):
    if checkpoint.stage == 'recoverable':
        checkpoint = record(service, checkpoint, lease, stage=checkpoint.previous_stage)
    try:
        checkpoint = await configure_profile(service, checkpoint, matrix, lease)
        checkpoint = await initialize_manager(service, checkpoint, matrix, lease)
        checkpoint = await start_manager(service, checkpoint, matrix, lease)
        observed = await observe_checkpoint(service, checkpoint, matrix)
        require_running(observed)
        if checkpoint.stage == 'completed':
            return checkpoint
        return stage(service, checkpoint, lease, 'completed', observed)
    except (OSError, ValueError, RuntimeError, TimeoutError):
        retained = service.journal.load()
        if retained is not None and not retained.installation_committed:
            record(service, retained, lease, stage='recoverable')
        raise LifecycleStateError('Scoped profile operation retained for explicit recovery; no uncertain cleanup was attempted.') from None


async def configure_profile(service, checkpoint, matrix, lease):
    if checkpoint.stage != 'intent':
        return checkpoint
    observed = await observe_checkpoint(service, checkpoint, matrix)
    if observed.instance_state != 'absent' or not observed.listeners_clear:
        raise LifecycleStateError('Profile creation precondition changed.')
    if observed.profile_state == 'absent':
        checkpoint, observed = await write_and_observe(service, checkpoint, matrix, lease, observed,
                                                      'profile-create', service.runtime.create_profile)
    if observed.profile_state != 'exact' or observed.instance_state != 'absent' or not observed.listeners_clear:
        raise LifecycleStateError('Dedicated profile creation postcondition is unproven.')
    return stage(service, checkpoint, lease, 'profile-configured', observed)


async def initialize_manager(service, checkpoint, matrix, lease):
    if checkpoint.stage != 'profile-configured':
        return checkpoint
    observed = await observe_checkpoint(service, checkpoint, matrix)
    if observed.profile_state != 'exact' or not observed.listeners_clear:
        raise LifecycleStateError('Stopped initialization precondition changed.')
    if observed.instance_state == 'absent':
        checkpoint, observed = await write_and_observe(service, checkpoint, matrix, lease, observed,
                                                      'instance-init', service.runtime.init_instance)
    require_stopped(observed)
    return stage(service, checkpoint, lease, 'instance-initialized', observed)


async def start_manager(service, checkpoint, matrix, lease):
    if checkpoint.stage == 'instance-initialized':
        observed = await observe_checkpoint(service, checkpoint, matrix)
        require_stopped(observed)
        checkpoint = stage(service, checkpoint, lease, 'routes-verified', observed)
    if checkpoint.stage != 'routes-verified':
        return checkpoint
    observed = await observe_checkpoint(service, checkpoint, matrix)
    if observed.instance_state == 'stopped':
        require_stopped(observed)
        checkpoint, observed = await write_and_observe(service, checkpoint, matrix, lease, observed,
                                                      'instance-start', service.runtime.start_instance)
    elif checkpoint.pending_action != 'instance-start':
        raise LifecycleStateError('An unrecorded manager start cannot be adopted.')
    require_running(observed)
    return stage(service, checkpoint, lease, 'instance-started', observed)


async def cleanup(service, checkpoint, matrix, lease):
    if (checkpoint.installation_committed or checkpoint.stage in {'instance-started', 'completed'}
            or checkpoint.previous_stage in {'instance-started', 'completed'}
            or checkpoint.pending_action == 'instance-start'):
        raise LifecycleStateError('Post-start state is retained for recovery; cleanup is refused.')
    observed = await observe_checkpoint(service, checkpoint, matrix)
    if checkpoint.stage == 'cleaned':
        if observed.profile_state != 'absent' or observed.instance_state != 'absent':
            raise LifecycleStateError('Cleaned targets reappeared; refuse adoption.')
        return checkpoint
    if observed.instance_state == 'stopped':
        require_stopped(observed)
        checkpoint, observed = await write_and_observe(service, checkpoint, matrix, lease, observed,
                                                      'instance-delete', service.runtime.delete_instance)
    if observed.instance_state != 'absent' or not observed.listeners_clear:
        raise LifecycleStateError('Stopped instance cleanup is uncertain; profile is retained.')
    if observed.profile_state == 'exact':
        checkpoint, observed = await write_and_observe(service, checkpoint, matrix, lease, observed,
                                                      'profile-delete', service.runtime.delete_profile)
    if observed.profile_state != 'absent' or observed.instance_state != 'absent':
        raise LifecycleStateError('Profile cleanup is uncertain; retained checkpoint is authoritative.')
    return stage(service, checkpoint, lease, 'cleaned', observed)


async def settle_effect(effect: Awaitable[None]) -> None:
    """Keep installation/journal ownership until an admitted child has settled."""
    worker = asyncio.ensure_future(effect)
    try:
        await asyncio.shield(worker)
    except asyncio.CancelledError:
        while not worker.done():
            try:
                await asyncio.shield(worker)
            except asyncio.CancelledError:
                continue
            except (OSError, ValueError, RuntimeError, TimeoutError):
                break
        # Consume the child exception without changing cancellation ownership.
        if worker.done() and not worker.cancelled():
            worker.exception()
        raise


async def observe_checkpoint(service, checkpoint, matrix):
    observed = await observe(service, checkpoint.intent, matrix)
    deleting = checkpoint.pending_action in {'instance-delete', 'profile-delete'} or checkpoint.stage == 'cleaned'
    if checkpoint.instance_uuid is not None:
        if observed.instance_uuid != checkpoint.instance_uuid and not (deleting and observed.instance_state == 'absent'):
            raise LifecycleStateError('The checkpoint-bound manager instance identity changed.')
    workers = {worker.node_name: worker for worker in observed.workers}
    if any(workers[name].instance_uuid != identity for name, identity in checkpoint.worker_uuids.items()):
        raise LifecycleStateError('Checkpoint-bound worker identity changed.')
    if checkpoint.pending_action is None and observed.observation_sha256 != checkpoint.observation_sha256:
        raise LifecycleStateError('Observed profile operation state changed before the next effect.')
    return observed


async def retained_cleanup(service, checkpoint, matrix, lease):
    try:
        return await cleanup(service, checkpoint, matrix, lease)
    except (OSError, ValueError, RuntimeError, TimeoutError):
        raise LifecycleStateError('Scoped cleanup is unverified; retain the original checkpoint and resources for explicit recovery.') from None


def committed_stack_policy(checkpoint, manifest):
    owners = manifest.effective_stack_ownership()
    if set(owners) != set(checkpoint.intent.planned_stack_owners):
        return False
    for name, mode in checkpoint.intent.planned_stack_owners.items():
        if owners[name].owner != mode:
            return False
        if mode == 'portainer' and owners[name] != checkpoint.verified_stack_ownership.get(name):
            return False
    return True
