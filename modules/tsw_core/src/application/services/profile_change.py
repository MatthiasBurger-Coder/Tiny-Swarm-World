"""Existing own-profile updates with durable intent and exact readback."""
from copy import copy

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.installation_profile import admitted_matrix, observe, require_running, settle_effect
from tiny_swarm_world.domain.lifecycle.models import PortainerOwnership
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import ProfileChangeCheckpoint, preserve_verified_portainer_identity, validate_profile_change_owner


class ProfileChangeOperation:
    def __init__(self, service, journal, intent, lease, plan, consent, *, recovery=False):
        self.service, self.journal, self.intent = service, journal, intent
        self.lease, self.plan, self.consent, self.recovery = lease, plan, consent, recovery

    @property
    def verified_stack_ownership(self):
        self.lease.require_active()
        checkpoint = self.require_checkpoint()
        return dict(checkpoint.verified_stack_ownership)

    def require_checkpoint(self):
        checkpoint = self.journal.load()
        if checkpoint is None or checkpoint.intent != self.intent:
            raise LifecycleStateError('Profile change requires the exact original intent.')
        return checkpoint

    async def admit_desired(self, plan):
        self.lease.require_active()
        snapshot = self.service.manifests.load()
        if snapshot.token == self.intent.manifest_token and snapshot.manifest != self.intent.before_manifest:
            raise LifecycleStateError('Profile change baseline manifest content differs from actual persisted authority.')
        accepted_target = self.recovery and snapshot.manifest is not None and self.target_manifest_matches(snapshot.manifest)
        if plan != self.plan or (snapshot.token != self.intent.manifest_token and not accepted_target):
            raise LifecycleStateError('Profile change desired state or baseline changed.')
        await self.inspect_current()

    async def inspect_current(self):
        matrix = admitted_matrix(self.service.capabilities, self.consent)
        checkpoint = self.journal.load()
        template = self.intent.target if checkpoint is not None and checkpoint.stage in {'verified', 'committed'} else self.intent.before
        try:
            return await inspect_template(self, template, matrix)
        except LifecycleStateError:
            if checkpoint is None or checkpoint.stage != 'pending':
                raise
            return await inspect_template(self, self.intent.target, matrix)

    async def ensure_manager(self):
        await self.admit_desired(self.plan)

    async def ensure_worker(self, node_name):
        await self.verify_node(node_name)

    async def verify_node(self, node_name):
        if node_name not in {self.intent.target.node_name, *(worker.node_name for worker in self.intent.target.workers)}:
            raise LifecycleStateError('Unselected existing node cannot join profile changes.')
        await self.admit_desired(self.plan)

    async def verify_effective_routes(self):
        await self.apply()

    async def apply(self):
        self.lease.require_active()
        with self.journal.exclusive(self.lease):
            checkpoint = self.require_checkpoint()
            matrix = admitted_matrix(self.service.capabilities, self.consent)
            if checkpoint.stage in {'verified', 'committed'}:
                await inspect_template(self, self.intent.target, matrix)
                return
            if checkpoint.stage == 'pending':
                if not self.recovery:
                    raise LifecycleStateError('Resume the original uncertain profile change explicitly.')
                try:
                    observed = await inspect_template(self, self.intent.target, matrix)
                except LifecycleStateError:
                    observed = await inspect_template(self, self.intent.before, matrix)
                else:
                    save(self, checkpoint, stage='verified', observation_sha256=observed.observation_sha256)
                    return
            else:
                observed = await inspect_template(self, self.intent.before, matrix)
            checkpoint = save(self, checkpoint, stage='pending', observation_sha256=observed.observation_sha256)
            fresh = await inspect_template(self, self.intent.before, matrix)
            if fresh.observation_sha256 != checkpoint.observation_sha256:
                raise LifecycleStateError('Profile changed after durable write intent.')
            private = self.service.runtime.for_operation(self.lease, self.intent.target)
            try:
                await settle_effect(private.update_profile(self.intent.target, self.intent.before))
            except (OSError, ValueError, RuntimeError, TimeoutError):
                pass
            observed = await inspect_template(self, self.intent.target, matrix)
            save(self, checkpoint, stage='verified', observation_sha256=observed.observation_sha256)

    async def record_stack_ownership(self, service_id, ownership):
        self.lease.require_active()
        try:
            checked = PortainerOwnership.model_validate_json(ownership.model_dump_json())
            validate_profile_change_owner(self.intent, service_id, checked)
        except (AttributeError, ValueError):
            raise LifecycleStateError('Selected Portainer ownership type or existing identity changed.') from None
        with self.journal.exclusive(self.lease):
            checkpoint = self.require_checkpoint()
            if checkpoint.stage not in {'verified', 'committed'}:
                raise LifecycleStateError('Ownership postconditions require the verified profile target.')
            previous = checkpoint.verified_stack_ownership.get(service_id)
            if previous is not None:
                try:
                    preserve_verified_portainer_identity(previous, checked)
                except ValueError:
                    raise LifecycleStateError('Durably verified managed-stack identity changed.') from None
            save(self, checkpoint, verified_stack_ownership={**checkpoint.verified_stack_ownership, service_id: checked})

    def target_manifest_matches(self, manifest):
        return target_manifest_matches(self, manifest)

    async def commit_installation(self):
        matrix = admitted_matrix(self.service.capabilities, self.consent)
        with self.journal.exclusive(self.lease):
            checkpoint = self.require_checkpoint()
            if checkpoint.stage not in {'verified', 'committed'}:
                raise LifecycleStateError('Profile change has no verified target.')
            await inspect_template(self, self.intent.target, matrix)
            manifest = self.service.manifests.load().manifest
            if manifest is None or not self.target_manifest_matches(manifest):
                raise LifecycleStateError('Profile change manifest commit is unproven.')
            if checkpoint.stage != 'committed':
                save(self, checkpoint, stage='committed')


async def inspect_template(operation, template, matrix):
    service = copy(operation.service)
    service.runtime = service.runtime.for_operation(operation.lease, template)
    observed = await observe(service, template, matrix)
    require_running(observed)
    if observed.instance_uuid != operation.intent.instance_uuid:
        raise LifecycleStateError('Existing manager identity changed.')
    workers = {worker.node_name: worker for worker in observed.workers}
    if (set(workers) != set(operation.intent.worker_uuids)
            or any(worker.state != 'running' or not worker.no_proxy
                   or worker.instance_uuid != operation.intent.worker_uuids[name] for name, worker in workers.items())):
        raise LifecycleStateError('Existing worker identity or effective no-proxy state changed.')
    return observed


def save(operation, checkpoint, **changes):
    payload = checkpoint.model_dump()
    payload.update(changes, generation=checkpoint.generation + 1)
    updated = ProfileChangeCheckpoint.model_validate(payload)
    operation.journal.save(updated, expected=checkpoint, lease=operation.lease)
    return updated


def target_manifest_matches(self, manifest):
    checkpoint = self.require_checkpoint()
    original, target = self.intent.before_manifest, self.intent.target.profile
    if (manifest.installation_id != original.installation_id or manifest.product != original.product
            or manifest.host != original.host
            or manifest.operation_reference != original.operation_reference
            or manifest.service_preset != getattr(self.plan, 'service_preset', original.service_preset)
            or manifest.selection_reasons != getattr(self.plan, 'selection_reasons', manifest.selection_reasons)
            or manifest.installation_profile != target.profile
            or manifest.requested_services != target.requested_services or manifest.resolved_services != target.resolved_services
            or manifest.service_exposure != target.service_exposure
            or manifest.checkpoint_reference != 'profile-change-' + self.intent.operation_id
            or any(component not in manifest.components for component in original.components)
            or any(reference not in manifest.credential_references for reference in original.credential_references)
            or any(reference not in manifest.configuration_references for reference in original.configuration_references)):
        return False
    owners = manifest.effective_stack_ownership()
    return set(owners) == set(self.intent.planned_stack_owners) and all(
        owners[name].owner == mode and (mode != 'portainer' or owners[name] == checkpoint.verified_stack_ownership.get(name))
        for name, mode in self.intent.planned_stack_owners.items())
