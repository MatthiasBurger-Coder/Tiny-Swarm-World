"""Canonical minimal-selection admission for deployment composition."""
from tiny_swarm_world.domain.deployment.service_stack_contract import DEFAULT_SERVICE_STACK_CONTRACTS


def minimal_apply_checks(selected, update_stack, contracts, application_steps, bootstrap_steps):
    canonical = next(contract for contract in DEFAULT_SERVICE_STACK_CONTRACTS if contract.stack_name == 'portainer')
    if (selected is None or len(selected) != 2 or set(selected) != {'incus', 'portainer'}
            or update_stack is not None or application_steps or contracts != (canonical,)):
        return ()
    required_targets = (
        'deployment:portainer-admin-access',
        'deployment:portainer-local-endpoint',
    )
    checks = {}
    for step in bootstrap_steps:
        target_id = getattr(step, 'verification_target_id', None)
        if target_id not in required_targets:
            continue
        if target_id in checks:
            return ()
        checks[target_id] = step
    if set(checks) != set(required_targets):
        return ()
    return tuple(checks[target_id] for target_id in required_targets)
