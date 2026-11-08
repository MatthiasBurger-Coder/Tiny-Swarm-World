"""Complete one original creation checkpoint after its exact manifest was adopted."""
from copy import copy

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.operation_result import OperationError
from tiny_swarm_world.application.services.installation_profile import (
    admitted_matrix, committed_stack_policy, observe_checkpoint, record, require_checkpoint, require_running,
)
from tiny_swarm_world.application.services.profile_setup import require_workers_running
from tiny_swarm_world.domain.lifecycle.profile_lifecycle import installation_manifest_sha256


def require_commit_candidate(checkpoint, manifest):
    intent = checkpoint.intent
    if (checkpoint.stage != 'completed' or checkpoint.pending_action is not None
            or manifest.schema_version != 2 or manifest.installation_id != intent.profile.installation_id
            or manifest.installation_profile != intent.profile.profile
            or manifest.checkpoint_reference != 'profile-' + intent.profile.operation_id
            or manifest.product.revision != intent.profile.product_source_revision
            or manifest.requested_services != intent.profile.requested_services
            or manifest.resolved_services != intent.profile.resolved_services
            or manifest.effective_exposure() != intent.profile.service_exposure
            or not committed_stack_policy(checkpoint, manifest)):
        raise LifecycleStateError('Original creation manifest and verified ownership differ.')


def bind_manifest_commit(operation, candidate):
    operation.lease.require_active()
    with operation.service.journal.exclusive(operation.lease):
        checkpoint = require_checkpoint(operation.service, operation.intent)
        require_commit_candidate(checkpoint, candidate)
        digest = installation_manifest_sha256(candidate)
        if checkpoint.installation_manifest_sha256 is not None:
            if checkpoint.installation_manifest_sha256 != digest:
                raise LifecycleStateError('Original installation candidate changed before adoption.')
            return
        if operation.service.manifests.load().manifest is not None:
            raise LifecycleStateError('Original installation commitment must precede adoption.')
        record(operation.service, checkpoint, operation.lease, installation_manifest_sha256=digest)


class CreationCompletionOperation:
    """Read-only original authority plus its final checkpoint mark; no runtime writer."""
    def __init__(self, service, checkpoint, lease, plan, consent, verify_deployments):
        self.service, self.intent, self.lease = copy(service), checkpoint.intent, lease
        self.plan, self.consent, self.verify_deployments = plan, consent, verify_deployments
        self.service.runtime = service.runtime.for_operation(lease, self.intent)

    async def admit_desired(self, plan):
        self.lease.require_active()
        snapshot = self.service.manifests.load()
        manifest = snapshot.manifest
        checkpoint = require_checkpoint(self.service, self.intent)
        if (manifest is None or snapshot.token != plan.manifest_token or plan != self.plan
                or checkpoint.installation_manifest_sha256 is None
                or installation_manifest_sha256(manifest) != checkpoint.installation_manifest_sha256
                or plan.requested_services != manifest.requested_services
                or plan.resolved_services != manifest.resolved_services
                or plan.service_exposure != manifest.effective_exposure()
                or plan.stack_owners != {name: owner.owner for name, owner in manifest.effective_stack_ownership().items()}):
            raise LifecycleStateError('Resume requires the exact originally committed creation manifest and policy.')
        require_commit_candidate(checkpoint, manifest)
        matrix = admitted_matrix(self.service.capabilities, self.consent)
        try:
            observed = await observe_checkpoint(self.service, checkpoint, matrix)
            require_running(observed)
            require_workers_running(checkpoint, observed)
            host = next(item for item in manifest.components if item.component_id == 'incus')
            for identity in (host.desired, host.observed):
                if identity is not None and (identity.upstream_version not in {None, observed.client_version}
                        or any(value is not None for key, value in identity.model_dump().items() if key != 'upstream_version')):
                    raise LifecycleStateError('Original Incus component identity is not proved by the current admitted daemon.')
            await self.verify_deployments(manifest)
        except (OperationError, OSError, RuntimeError, TimeoutError):
            raise LifecycleStateError('Original creation completion runtime readback is unavailable; preserve state.') from None

    async def commit_installation(self):
        await self.admit_desired(self.plan)
        await self.service.commit_installation(self.intent, consent=self.consent, lease=self.lease)
