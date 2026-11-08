"""Write-ahead create receipts and guarded existing-definition updates."""
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.shared.settled_blocking import settled_blocking


async def ensure_created(operation, intent, definition, environment, endpoint, owner):
    identifier = owner.stack_id if owner is not None else intent.created_stack_id
    if identifier is None:
        if intent.phase == 'uncertain':
            raise LifecycleStateError('Managed create outcome is uncertain without a returned ID; operator recovery required.')
        await settled_blocking(operation.api.require_absent, definition.name, endpoint)
        intent = operation._save(intent, phase='uncertain')
        operation.lease.require_active()
        receipt = await settled_blocking(operation.api.create, definition, endpoint, environment)
        identifier = receipt.stack_id
        intent = operation._save(intent, phase='received', created_stack_id=identifier,
            created_resource_control_id=receipt.resource_control_id, created_ownership_fingerprint=receipt.ownership_fingerprint)
    return intent, identifier


def require_created_identity(intent, observed, owner):
    if owner is None and (observed.ownership.resource_control_id != intent.created_resource_control_id
            or observed.ownership.ownership_fingerprint != intent.created_ownership_fingerprint):
        raise LifecycleStateError('Created stack ownership differs from the durably captured response identity.')


async def update_existing(operation, intent, observed, owner, definition, fingerprint):
    if owner is not None:
        if observed.ownership.definition_fingerprint != fingerprint:
            if observed.ownership != owner:
                raise LifecycleStateError('Managed source ownership/definition drifted; no update is allowed.')
            intent = operation._save(intent, phase='uncertain')
            operation.lease.require_active()
            await settled_blocking(operation.api.update, observed, definition)
            intent = operation._save(intent, phase='received')
        elif observed.ownership.model_copy(update={'definition_fingerprint': owner.definition_fingerprint}) != owner:
            raise LifecycleStateError('Managed ownership identity changed; refuse same-name adoption.')
    return intent
