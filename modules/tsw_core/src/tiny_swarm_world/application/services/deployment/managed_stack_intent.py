"""Admission and exact forward/reverse intent selection before managed writes."""
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.shared.settled_blocking import settled_blocking
from tiny_swarm_world.domain.lifecycle.managed_stack import ManagedStackIntent


def matches_intent(operation, prior, name, endpoint, fingerprint, owner):
    return (prior.installation_id == operation.installation_id and prior.stack_name == name
            and prior.endpoint_id == endpoint and prior.target_fingerprint == fingerprint
            and owner in (prior.source, prior.result))


def admitted_prior(operation, name, endpoint, images, owner):
    if not images or (owner is not None and owner.endpoint_id != endpoint):
        raise LifecycleStateError('Managed stack endpoint or target image inventory differs.')
    prior = operation.journal.load()
    if prior is not None and (prior.installation_id != operation.installation_id
            or prior.stack_name != name or prior.endpoint_id != endpoint):
        raise LifecycleStateError('Managed journal belongs to another installation or endpoint.')
    return prior


def recovery_owner(prior, owner, recovery):
    if recovery and prior is not None and prior.recovery_of is not None and prior.source is not None and owner is not None:
        if prior.source.model_copy(update={'definition_fingerprint': owner.definition_fingerprint}) != owner:
            raise LifecycleStateError('Recovery source identity differs from the original owner.')
        return prior.source
    return owner


def select_intent(operation, prior, name, endpoint, fingerprint, owner, recovery):
    reusable = prior is not None and matches_intent(operation, prior, name, endpoint, fingerprint, owner)
    reversing = recovery and prior is not None and prior.target_fingerprint != fingerprint
    if prior is not None and not reversing and (prior.phase != 'verified' or reusable):
        if not matches_intent(operation, prior, name, endpoint, fingerprint, owner):
            raise LifecycleStateError('Resume the original managed-stack operation and exact definition.')
        return prior
    intent = ManagedStackIntent(installation_id=operation.installation_id, operation_id=operation.lease.operation_id,
        stack_name=name, endpoint_id=endpoint, target_fingerprint=fingerprint, source=owner)
    if not reversing:
        operation.journal.save(intent)
    return intent


async def prepare_recovery(operation, intent, prior, name, endpoint, fingerprint, owner, recovery):
    if recovery and prior is not None and owner is not None:
        current = (await settled_blocking(operation.api.inspect, name, endpoint, owner.stack_id)).ownership
        if current.model_copy(update={'definition_fingerprint': owner.definition_fingerprint}) != owner:
            raise LifecycleStateError('Recovery ownership changed outside the original transition.')
        if prior.target_fingerprint != fingerprint:
            if prior.source is None or current.definition_fingerprint not in {prior.source.definition_fingerprint, prior.target_fingerprint}:
                raise LifecycleStateError('Recovery cannot reverse an unknown managed definition.')
            intent = ManagedStackIntent(installation_id=operation.installation_id, operation_id=operation.lease.operation_id,
                stack_name=name, endpoint_id=endpoint, target_fingerprint=fingerprint, source=current,
                recovery_of=prior.target_fingerprint, recovery_source=prior.source)
            operation.journal.save(intent)
        owner = intent.source
    return intent, owner
