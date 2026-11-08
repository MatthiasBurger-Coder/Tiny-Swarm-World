"""Route selected image transitions through their persisted management writer."""
from copy import copy
from collections.abc import Callable
from pathlib import Path

import yaml

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.lifecycle.installation_profile import require_legacy_runtime_policy
from tiny_swarm_world.application.services.deployment.managed_stack import ManagedStackOperation
from tiny_swarm_world.application.services.shared.settled_blocking import settled_blocking
from tiny_swarm_world.domain.deployment.stack_definition import StackDefinition
from tiny_swarm_world.domain.lifecycle.models import PortainerOwnership
from tiny_swarm_world.infrastructure.adapters.lifecycle.component_runtime import image_reference, compose_service
from tiny_swarm_world.infrastructure.adapters.lifecycle.managed_stack_api import GuardedPortainerStackApi, definition_fingerprint
from tiny_swarm_world.infrastructure.adapters.lifecycle.managed_stack_journal import JsonManagedStackJournal


class ManagedComponentRuntime:
    def __init__(self, delegate, manifests, root: Path, api: GuardedPortainerStackApi, observer,
                 operation_factory: Callable):
        self.delegate, self.manifests, self.root = delegate, manifests, root
        self.api, self.observer, self.operation_factory = api, observer, operation_factory
        self.lease = None
        self.operation = None
        self.verified_stack_ownership: dict[str, PortainerOwnership] = {}

    def for_operation(self, lease):
        result = copy(self)
        result.lease = lease
        result.delegate = self.delegate.for_operation(lease)
        result.verified_stack_ownership = {}
        return result

    @property
    def profile_intent(self):
        return None if self.operation is None else self.operation.intent.profile

    async def admit_runtime(self, consent, *, recovery):
        from tiny_swarm_world.application.services.runtime_policy import admit_runtime_policy

        snapshot = self.manifests.load()
        if snapshot.manifest is None:
            raise LifecycleStateError('Installation state missing before runtime admission.')
        self.operation = await admit_runtime_policy(snapshot.manifest, self.lease,
            'recovery' if recovery else 'component-update', consent, self.operation_factory)

    def validate_manifest(self, manifest):
        if manifest.installation_profile is None:
            require_legacy_runtime_policy(manifest)
        elif self.operation is None:
            raise LifecycleStateError('Scoped component updates require explicit profile runtime admission.')
        else:
            self.operation.intent.profile.validate_manifest(manifest)

    def validate(self, stages):
        self.delegate.validate(stages)

    async def transition(self, stage, consent, *, recovery):
        from tiny_swarm_world.application.ports.operation_result import OperationError

        try:
            return await self._transition(stage, consent, recovery=recovery)
        except (OperationError, OSError, RuntimeError, TimeoutError, ValueError):
            return False

    async def _transition(self, stage, consent, *, recovery):
        snapshot = self.manifests.load()
        if snapshot.manifest is None or self.lease is None or not consent.accepted:
            raise LifecycleStateError('Component update lacks admitted installation state/lease/consent.')
        manifest = snapshot.manifest
        owner = manifest.effective_stack_ownership().get(stage.service_id)
        if manifest.installation_profile is not None:
            operation = await self.operation_factory(manifest, self.lease, 'recovery' if recovery else 'component-update', consent)
        else:
            operation = None
        if not isinstance(owner, PortainerOwnership):
            if operation is None:
                return await self.delegate.transition(stage, consent, recovery=recovery)
            # The direct-Swarm delegate still requires an explicit admitted scope;
            # the operation is attached privately, never to a shared factory.
            self.delegate.workflow.profile_operation = operation
            return await self.delegate.transition(stage, consent, recovery=recovery)
        if operation is None:
            raise LifecycleStateError('Portainer-owned update requires an admitted profile runtime operation.')
        current = await settled_blocking(self.api.inspect, stage.service_id, owner.endpoint_id, owner.stack_id)
        pending = JsonManagedStackJournal(self.root / '.tiny-swarm-world/installation' / f'managed-stack-{stage.service_id}.json', self.lease)
        previous = pending.load()
        if current.ownership != owner and (previous is None or previous.source is None
                or previous.source.model_copy(update={'definition_fingerprint': owner.definition_fingerprint}) != owner
                or current.ownership.definition_fingerprint not in {previous.source.definition_fingerprint, previous.target_fingerprint}):
            raise LifecycleStateError('Saved component definition drifted outside this transition.')
        payload = yaml.safe_load(current.definition.compose_content)
        member = compose_service(stage)
        if not isinstance(payload, dict) or member not in payload.get('services', {}):
            raise LifecycleStateError('Recorded component is absent from managed definition.')
        expected = image_reference(stage.source if recovery else stage.target)
        payload['services'][member]['image'] = expected
        target = StackDefinition(name=stage.service_id, compose_content=yaml.safe_dump(payload, sort_keys=True))
        images = {name: item['image'] for name, item in payload['services'].items()}
        if any(not isinstance(value, str) or '${' in value for value in images.values()):
            raise LifecycleStateError('Managed update requires already pinned/resolved complete image definitions.')
        runtime = ManagedStackOperation(self.api, pending, self.observer,
            installation_id=manifest.installation_id, lease=self.lease)
        async def verified(value):
            await operation.verify_effective_routes()
            self.verified_stack_ownership[stage.service_id] = value
            await operation.record_stack_ownership(stage.service_id, value)
        await runtime.apply(target, current.environment, images, definition_fingerprint(target, current.environment),
                            owner, verified, recovery=recovery)
        return True
