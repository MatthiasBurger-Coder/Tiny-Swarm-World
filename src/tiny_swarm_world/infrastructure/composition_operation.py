"""Installation operation wiring shared by setup and Classic composition."""
import os
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, TypedDict

from tiny_swarm_world.infrastructure.project_paths import default_project_paths
from tiny_swarm_world.application.services.platform.workflow.update import ClassicUpdateWorkflow
from tiny_swarm_world.domain.update import image_override_environment_name
from tiny_swarm_world.infrastructure.adapters.update import JsonUpdateStateStore
from tiny_swarm_world.infrastructure.adapters.update.lxc_runtime_observer import LxcUpdateRuntimeObserver
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.manager_shell_gateway import LxcManagerShellGateway
from tiny_swarm_world.infrastructure.logging.logger_factory import LoggerFactory
from tiny_swarm_world.application.ports.lifecycle.installation_profile import InstallationLease, InstallationOperationLock
from tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock import (
    JsonInstallationOperationLock, bind_operation_lease, locked_setup_services, require_anchor_runtime_policy,
)


async def run_setup_operation(root: Path, lease: InstallationLease | None,
                              invoke: Callable[[InstallationLease], Awaitable[Any]], *, profile_operation=None) -> Any:
    lock = JsonInstallationOperationLock(root)
    with lock.exclusive('setup', lease=lease) as admitted:
        if profile_operation is None:
            require_anchor_runtime_policy(root)
        else:
            from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError

            if profile_operation.lease is not admitted:
                raise LifecycleStateError('Scoped setup operation belongs to another installation lease.')
            admit_runtime = getattr(profile_operation, 'admit_runtime', None)
            if callable(admit_runtime):
                await admit_runtime()
            else:
                await profile_operation.admit_desired(profile_operation.plan)
        return await invoke(admitted)


def private_services(services: Any, lease: InstallationLease | None) -> Any:
    return bind_operation_lease(services, lease)


def setup_services(services: Any, root: Path, factory: Callable[[InstallationLease], Any],
                   lease: InstallationLease | None, *, profile_operation=None) -> Any:
    return locked_setup_services(services, root, factory, lease,
                                 **({'profile_operation': profile_operation} if profile_operation is not None else {}))


class ClassicOperationArguments(TypedDict):
    operation_lock: InstallationOperationLock
    mutation_policy_guard: Callable[[], None]


def classic_operation_arguments(root: Path) -> ClassicOperationArguments:
    return {'operation_lock': JsonInstallationOperationLock(root),
            'mutation_policy_guard': lambda: require_anchor_runtime_policy(root)}


def build_classic_workflow(facade, runtime, root_factory, service_profile, node_provider_request):
    compose_repository = facade.build_compose_file_repository(
        service_profile=service_profile,
    )
    provider_request = node_provider_request or runtime._default_node_provider_request()
    backend = runtime._lxc_backend_for_provider_request(provider_request)
    observer = (
        LxcUpdateRuntimeObserver(LxcManagerShellGateway(
            backend=backend,
            manager_node="swarm-manager",
            timeout_seconds=10,
            logger=LoggerFactory.get_logger("classic_update_observer"),
            process_runner=facade.build_process_runner(),
        ))
        if backend is not None else None
    )

    def deployment_workflow_for(plan, *, operation_lease=None):
        image_environment = image_override_environment_name(
            plan.stack_name,
            plan.service_name,
        )
        services = facade.build_deployment_services_for_provider(
            service_profile=service_profile,
            node_provider_request=node_provider_request,
            image_overrides={image_environment: plan.target_image},
            update_stack_name=plan.stack_name,
        )
        delegated_services = private_services(services, operation_lease)
        return delegated_services.workflows.apply

    configured_state_root = os.environ.get("TSW_UPDATE_STATE_ROOT", "").strip()
    if configured_state_root:
        state_root = Path(configured_state_root).expanduser()
    else:
        state_home = os.environ.get("XDG_STATE_HOME", "").strip()
        state_root = (
            Path(state_home).expanduser() if state_home else Path.home() / ".local" / "state"
        ) / "tiny-swarm-world" / "updates"
    workflow = ClassicUpdateWorkflow(
        compose_repository=compose_repository,
        deployment_workflow_factory=deployment_workflow_for,
        state_store=JsonUpdateStateStore(state_root),
        runtime_observer=observer,
        **classic_operation_arguments(root_factory().repository_root),
    )
    return workflow


async def run_operation_cli(workflow, confirmation, live_consent, service_profile,
                            node_provider_request, allow_wsl_windows_filesystem, update_plan,
                            update_preview, update_recover, update_stack_name, update_service_name,
                            *, fallback, execute, classic_factory, platform_factory,
                            artifact_factory, deployment_factory, setup_runner):
    mutation_actions = {'init', 'reconcile', 'expose', 'reset', 'destroy', 'repair-lxc-proxy-drift',
                        'docker', 'swarm-bootstrap', 'apply', 'bootstrap', 'run', 'update', 'recover', 'prepare'}
    if update_preview or workflow.action not in mutation_actions or live_consent is None or not live_consent.accepted:
        return await fallback(workflow, confirmation, live_consent, service_profile,
            node_provider_request, allow_wsl_windows_filesystem, update_plan, update_preview,
            update_recover, update_stack_name, update_service_name)
    lock = JsonInstallationOperationLock(default_project_paths().repository_root)
    with lock.exclusive('platform') as lease:
        require_anchor_runtime_policy(lock.root)
        def composed(factory):
            def build(*args, **kwargs):
                child = factory(*args, **kwargs)
                return bind_operation_lease(child, lease)
            return build
        async def setup(*args, **kwargs):
            return await setup_runner(*args, operation_lease=lease, **kwargs)
        return await execute(namespace=workflow.namespace, action=workflow.action,
            platform_kind=workflow.platform_kind, confirmation=confirmation, live_consent=live_consent,
            service_profile=service_profile, node_provider_request=node_provider_request,
            allow_wsl_windows_filesystem=allow_wsl_windows_filesystem, update_plan=update_plan,
            update_preview=update_preview, update_recover=update_recover,
            update_stack_name=update_stack_name, update_service_name=update_service_name,
            build_classic_update_workflow=composed(classic_factory),
            build_platform_services=composed(platform_factory),
            build_artifact_services=composed(artifact_factory),
            build_deployment_services=composed(deployment_factory),
            run_setup_with_terminal_status=setup)
