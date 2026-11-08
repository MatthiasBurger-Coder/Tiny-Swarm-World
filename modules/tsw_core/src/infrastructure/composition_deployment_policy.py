"""Selected readiness and operation-bound management writer composition."""
from tiny_swarm_world.application.services.deployment.verify_host_prerequisites import VerifyHostPrerequisites as VerifyHostPrerequisites
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.infrastructure.adapters.host import NativeLinuxHostPreparation as NativeLinuxHostPreparation
from tiny_swarm_world.infrastructure.adapters.host.host_environment_detector import HostEnvironmentDetector as HostEnvironmentDetector
from tiny_swarm_world.infrastructure.composition_internal_readiness import InternalSwaggerReadinessCheck as InternalSwaggerReadinessCheck


def host_prerequisites(detector, native_preparation, verify):
    environment = detector().detect().environment
    if environment is HostEnvironmentKind.WSL2:
        return ()
    return (verify(native_preparation()
        if environment is HostEnvironmentKind.NATIVE_LINUX else None),)


def managed_stack_steps(steps, operation, *, root, client, runtime, repository, backend, swarm):
    if operation is None:
        return
    from tiny_swarm_world.application.services.deployment.ensure_managed_stack import EnsureManagedStack
    from tiny_swarm_world.infrastructure.composition_management import ManagedDeploymentWriter

    for name, mode in operation.intent.planned_stack_owners.items():
        if mode != 'portainer' or name not in steps:
            continue
        ordinary = steps[name]
        writer = ManagedDeploymentWriter(root=root, profile_operation=operation, client=client,
            runtime=runtime, compose_repository=repository, backend=backend)
        steps[name] = EnsureManagedStack(compose_repository=repository, swarm_runtime=swarm,
            service_stack=ordinary.service_stack, stack_environment=ordinary.stack_environment,
            credential_snapshot=ordinary.credential_snapshot, credential_keys=ordinary.credential_keys,
            apply_managed=writer.apply)


def readiness_checks(contracts, runtime, exposure, endpoint_check, internal_check):
    return tuple(internal_check(contract, runtime.internal_swagger_ready)
        if contract.stack_name == 'swagger' and exposure is not None and exposure.get('swagger') == 'internal'
        else endpoint_check(service_stack=contract, max_attempts=60, wait_seconds=5)
        for contract in contracts)
