"""Local lifecycle state composition without runtime initialization."""
from pathlib import Path
from typing import Any


def build_installation_lifecycle_service(repository_root: Path | None = None) -> Any:
    """Compose local read-only inspection without runtime probes or logger setup."""
    from tiny_swarm_world.application.services.lifecycle import InstallationLifecycleService
    from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog
    from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
    from tiny_swarm_world.infrastructure.adapters.repositories.local_state_paths import local_state_file
    from tiny_swarm_world.infrastructure.project_paths import default_project_paths

    root = repository_root or default_project_paths().repository_root
    from tiny_swarm_world.infrastructure.adapters.lifecycle.installation_operation_lock import JsonInstallationOperationLock

    return InstallationLifecycleService(
        JsonManifestRepository(local_state_file(root=root, relative_path="installation/manifest.json")),
        NativeComponentCatalog(root), operation_lock=JsonInstallationOperationLock(root),
    )


async def prepare_setup_selection_state(lifecycle, plan, backend, runner, *, operation_lease=None, consent=None, recovery=False):
    """Admit selected setup through bounded inventory before runtime composition."""
    import asyncio
    from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
    from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
    from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.backend_cli import backend_cli
    from tiny_swarm_world.infrastructure.adapters.host.host_environment_detector import HostEnvironmentDetector
    from tiny_swarm_world.infrastructure.adapters.lifecycle.setup_state import SetupSelectionState
    from tiny_swarm_world.infrastructure.adapters.repositories.node_provider_config_yaml_repository import NodeProviderConfigYamlRepository
    from tiny_swarm_world.infrastructure.project_paths import default_project_paths
    from .composition_profile import prepare_profile_state

    if backend is None:
        raise LifecycleStateError("Selective setup requires a resolved Incus backend; prepare the host and retry.")
    host = HostEnvironmentDetector().detect().environment
    if host not in {HostEnvironmentKind.NATIVE_LINUX, HostEnvironmentKind.WSL2}:
        raise LifecycleStateError("Selective setup requires supported native Linux or WSL2.")
    paths = default_project_paths()
    state = SetupSelectionState(lifecycle, plan, paths.repository_root)
    state.operation_lease = operation_lease
    config = NodeProviderConfigYamlRepository(project_paths=paths).load()
    recover_manifest = None
    if recovery and lifecycle.manifests.load().manifest is None:
        from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_journal import JsonProfileLifecycleJournal
        retained = JsonProfileLifecycleJournal(paths.repository_root).load()
        if retained is None or retained.intent.initial_manifest is None:
            raise LifecycleStateError('No original scoped setup checkpoint exists.')
        recover_manifest = retained.intent.initial_manifest
    await asyncio.to_thread(state.admit, runner, backend=backend_cli(backend),
                            node_names=tuple(node.spec.name for node in config.nodes),
                            host="native-linux" if host is HostEnvironmentKind.NATIVE_LINUX else "wsl2",
                            recover_manifest=recover_manifest)
    state.profile_operation = await prepare_profile_state(state, config, consent, operation_lease, recovery=recovery)
    await state.admit_exposure()
    return state


async def complete_setup_selection_state(state, backend, runner):
    """Observe new pinned components only after the existing setup/auth checks passed."""
    import logging
    from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
    from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.manager_shell_gateway import LxcManagerShellGateway
    from tiny_swarm_world.infrastructure.adapters.update.lxc_runtime_observer import LxcUpdateRuntimeObserver

    if not state.observation_required:
        return
    if backend is None:
        raise LifecycleStateError("Source observation requires the admitted Incus backend.")
    observer = LxcUpdateRuntimeObserver(LxcManagerShellGateway(
        backend=backend, manager_node="swarm-manager", timeout_seconds=10,
        logger=logging.getLogger("setup_source_observer"), process_runner=runner,
    ))
    await state.observe_new_components(observer)


def build_component_update_execution(lifecycle, node_provider_request=None, *, classic_workflow_factory):
    """Reuse Classic runtime adapters and installation-local durable state."""
    from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
    from tiny_swarm_world.application.services.component_execution import ComponentUpdateExecution
    from tiny_swarm_world.application.services.component_updates import ComponentUpdateService
    from tiny_swarm_world.infrastructure.adapters.lifecycle.component_runtime import ClassicComponentRuntime
    from tiny_swarm_world.infrastructure.adapters.lifecycle.update_journal import JsonUpdateJournal
    from tiny_swarm_world.infrastructure.adapters.repositories.local_state_paths import local_state_file

    snapshot = lifecycle.manifests.load()
    if snapshot.manifest is None:
        raise LifecycleStateError('Installation adoption required before component execution.')
    journal_path = lifecycle.manifests.path.parent / 'component-update.json'
    # Resolve the configured repository location through the same state-path policy.
    root = lifecycle.catalog.root
    if journal_path != local_state_file(root=root, relative_path='installation/component-update.json'):
        raise LifecycleStateError('Component update requires canonical installation state.')
    from typing import Any

    runtime: Any = ClassicComponentRuntime(classic_workflow_factory(
        service_profile=snapshot.manifest.service_preset, node_provider_request=node_provider_request))
    if snapshot.manifest.installation_profile is not None:
        from tiny_swarm_world.infrastructure.adapters.lifecycle.managed_component_runtime import ManagedComponentRuntime
        from tiny_swarm_world.infrastructure.adapters.lifecycle.managed_stack_api import GuardedPortainerStackApi
        from tiny_swarm_world.infrastructure.adapters.clients.lxc.services.lxc_portainer_http_client import LxcPortainerHttpClient
        from tiny_swarm_world.infrastructure.composition_configuration import _required_operator_secret_value

        observer = runtime.workflow.runtime_observer
        if observer is None:
            raise LifecycleStateError('Scoped component runtime observer is unavailable.')
        gateway = observer.gateway
        client = LxcPortainerHttpClient(backend=gateway.backend, username='admin',
            password=_required_operator_secret_value('TSW_PORTAINER_ADMIN_PASSWORD'))
        def swarm_identity():
            result = gateway.run_manager_shell("docker info --format '{{.Swarm.Cluster.ID}}'", check=False)
            if result.returncode:
                raise LifecycleStateError('Local Swarm identity unavailable.')
            return result.stdout.strip()
        runtime = ManagedComponentRuntime(runtime, lifecycle.manifests, root,
            GuardedPortainerStackApi(client._client(), swarm_identity), observer, profile_runtime_factory(lifecycle))
    return ComponentUpdateExecution(ComponentUpdateService(lifecycle.manifests, lifecycle.catalog),
                                    lifecycle.manifests, JsonUpdateJournal(journal_path), runtime, operation_lock=lifecycle.operation_lock)



def build_component_update_journal(lifecycle):
    from tiny_swarm_world.infrastructure.adapters.lifecycle.update_journal import JsonUpdateJournal

    return JsonUpdateJournal(lifecycle.manifests.path.parent / 'component-update.json')


def build_portainer_upgrade(lifecycle, node_provider_request=None, *, resolve_profile, required_secret):
    """Compose the dedicated gateway path with the existing manager-shell runtime."""
    import logging
    from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
    from tiny_swarm_world.application.services.portainer_upgrade import PortainerUpgradeService
    from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.manager_shell_gateway import LxcManagerShellGateway
    from tiny_swarm_world.infrastructure.adapters.clients.lxc.services.lxc_portainer_http_client import LxcPortainerHttpClient
    from tiny_swarm_world.infrastructure.adapters.lifecycle.portainer_journal import JsonPortainerJournal
    from tiny_swarm_world.infrastructure.adapters.lifecycle.portainer_runtime import ClassicPortainerUpgradeRuntime

    snapshot = lifecycle.manifests.load()
    if snapshot.manifest is None:
        raise LifecycleStateError('Adopt installation state before Portainer upgrade.')
    profile = resolve_profile(snapshot.manifest.service_preset, node_provider_request)
    if profile.backend is None:
        raise LifecycleStateError('Portainer upgrade requires a supported Classic Incus runtime.')
    password = required_secret('TSW_PORTAINER_ADMIN_PASSWORD')
    client = LxcPortainerHttpClient(backend=profile.backend, username='admin', password=password)
    shell = LxcManagerShellGateway(backend=profile.backend, manager_node='swarm-manager',
                                   timeout_seconds=300, logger=logging.getLogger('PortainerUpgrade'))
    runtime = ClassicPortainerUpgradeRuntime(shell, client._client(), managed_stacks=tuple(
        name for name, owner in snapshot.manifest.effective_stack_ownership().items() if owner.owner == 'portainer'),
        managed_ownership={name: owner for name, owner in snapshot.manifest.effective_stack_ownership().items() if owner.owner == 'portainer'})
    journal = JsonPortainerJournal(lifecycle.manifests.path.parent / 'portainer-upgrade.json')
    return PortainerUpgradeService(lifecycle.manifests, journal, runtime, operation_lock=lifecycle.operation_lock,
                                  profile_runtime_factory=profile_runtime_factory(lifecycle))


def build_portainer_upgrade_journal(lifecycle):
    from tiny_swarm_world.infrastructure.adapters.lifecycle.portainer_journal import JsonPortainerJournal

    return JsonPortainerJournal(lifecycle.manifests.path.parent / 'portainer-upgrade.json')


def profile_runtime_factory(lifecycle):
    """Each caller receives one explicitly leased, observed runtime authority."""
    async def admit(manifest, lease, kind, consent):
        from tiny_swarm_world.infrastructure.adapters.lifecycle.profile_setup import for_runtime

        operation = await for_runtime(lifecycle.catalog.root, lifecycle, lease, kind, consent)
        operation.intent.profile.validate_manifest(manifest)
        return operation
    return admit
