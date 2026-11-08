"""Artifact composition boundary.

Concrete artifacts service construction lives in this focused
infrastructure module. Runtime compatibility symbols are refreshed before
calls so legacy facade patch points remain effective.
"""

from __future__ import annotations

from .composition_selection import persisted_runtime_selection, artifact_contexts


from tiny_swarm_world.infrastructure.composition_configuration import (
    ContainerImageContract,
)

from .composition_runtime import (
    ArtifactPrepareStep,
    ArtifactPrepareWorkflow,
    ArtifactServices,
    ArtifactVerifyCheck,
    ArtifactVerifyWorkflow,
    ArtifactWorkflowKind,
    ArtifactWorkflows,
    DEFAULT_LXC_PLATFORM_NODES,
    EnsureContainerImage,
    EnsureNexusAdminAccess,
    EnsureNexusDockerHostedRepository,
    EnsureNexusDockerProxyRepository,
    EnsureNexusMavenProxyRepository,
    LXC_BACKEND_REQUIRED_REASON,
    LxcContainerImagePublisher,
    LxcContainerRuntime,
    LxcNexusHttpClient,
    ManagedLxcBackend,
    NexusDockerHostedRepositoryConfiguration,
    NexusDockerProxyRepositoryConfiguration,
    NexusMavenProxyRepositoryConfiguration,
    NodeProviderSelectionRequest,
    Path,
    ProcessRunner,
    PortUI,
    PortWorkflowProgress,
    WaitForNexusReady,
    _BlockedArtifactWorkflow,
    _container_image_contracts_from_environment,
    _default_node_provider_request,
    _lxc_backend_for_provider_request,
    _nexus_docker_hub_proxy_port,
    _nexus_docker_hub_proxy_repository_name,
    _nexus_docker_proxy_remote_url,
    _operator_secret_value,
    build_process_runner,
    cast,
    default_project_paths,
)
from . import composition_runtime as _runtime

_BOUNDARY_FUNCTION_NAMES = frozenset(["build_artifact_services_for_provider","build_lxc_artifact_services"])
_RUNTIME_SYMBOL_NAMES = frozenset(["ArtifactPrepareStep","ArtifactPrepareWorkflow","ArtifactServices","ArtifactVerifyCheck","ArtifactVerifyWorkflow","ArtifactWorkflowKind","ArtifactWorkflows","DEFAULT_LXC_PLATFORM_NODES","EnsureContainerImage","EnsureNexusAdminAccess","EnsureNexusDockerHostedRepository","EnsureNexusDockerProxyRepository","EnsureNexusMavenProxyRepository","LXC_BACKEND_REQUIRED_REASON","LxcContainerImagePublisher","LxcContainerRuntime","LxcNexusHttpClient","ManagedLxcBackend","NexusDockerHostedRepositoryConfiguration","NexusDockerProxyRepositoryConfiguration","NexusMavenProxyRepositoryConfiguration","NodeProviderSelectionRequest","PortUI","PortWorkflowProgress","WaitForNexusReady","_BlockedArtifactWorkflow","_container_image_contracts_from_environment","_default_node_provider_request","_lxc_backend_for_provider_request","_nexus_docker_hub_proxy_port","_nexus_docker_hub_proxy_repository_name","_nexus_docker_proxy_remote_url","_operator_secret_value","build_process_runner","cast","default_project_paths","build_artifact_services_for_provider","build_lxc_artifact_services"])


def _refresh_runtime_symbols() -> None:
    for name in _RUNTIME_SYMBOL_NAMES:
        if name not in _BOUNDARY_FUNCTION_NAMES:
            globals()[name] = getattr(_runtime, name)


_refresh_runtime_symbols()


def build_artifact_services_for_provider(
    node_provider_request: NodeProviderSelectionRequest | None = None,
    ui: PortUI | None = None,
    progress: PortWorkflowProgress | None = None,
    resolved_services: tuple[str, ...] | None = None,
) -> ArtifactServices:
    provider_request = node_provider_request or _default_node_provider_request()
    backend = _lxc_backend_for_provider_request(provider_request)
    if backend is not None:
        return build_lxc_artifact_services(
            backend=backend, ui=ui, progress=progress,
            **({"resolved_services": resolved_services} if resolved_services is not None else {}),
        )
    return ArtifactServices(
        workflows=ArtifactWorkflows(
            prepare=cast(
                ArtifactPrepareWorkflow,
                _BlockedArtifactWorkflow(
                    ArtifactWorkflowKind.PREPARE,
                    LXC_BACKEND_REQUIRED_REASON,
                ),
            ),
            verify=cast(
                ArtifactVerifyWorkflow,
                _BlockedArtifactWorkflow(
                    ArtifactWorkflowKind.VERIFY,
                    LXC_BACKEND_REQUIRED_REASON,
                ),
            ),
        )
    )

def build_lxc_artifact_services(
    *,
    backend: ManagedLxcBackend,
    ui: PortUI | None = None,
    progress: PortWorkflowProgress | None = None,
    resolved_services: tuple[str, ...] | None = None,
) -> ArtifactServices:
    _, resolved_services = persisted_runtime_selection("default", resolved_services)
    project_paths = default_project_paths()
    process_runner = build_process_runner()
    contracts = _selected_image_contracts(resolved_services, project_paths.repository_root)
    requires_nexus = resolved_services is None or "nexus" in resolved_services
    nexus_admin_password = _operator_secret_value("TSW_NEXUS_ADMIN_PASSWORD") if requires_nexus else ""
    image_publisher = LxcContainerImagePublisher(
        backend=backend,
        process_runner=process_runner,
        registry_username="admin",
        registry_password=nexus_admin_password,
        project_paths=project_paths,
    )
    bootstrap_steps = (
        _nexus_bootstrap_steps(backend, process_runner, nexus_admin_password, ui, progress)
        if requires_nexus else ()
    )
    image_steps = tuple(EnsureContainerImage(image_publisher, contract) for contract in contracts)
    checks = cast(
        tuple[ArtifactPrepareStep, ...],
        (
            *bootstrap_steps,
            *image_steps,
        ),
    )
    verify_checks = cast(tuple[ArtifactVerifyCheck, ...], checks)
    return ArtifactServices(
        workflows=ArtifactWorkflows(
            prepare=ArtifactPrepareWorkflow(
                checks, bootstrap_steps=bootstrap_steps, requires_bootstrap=requires_nexus,
            ),
            verify=ArtifactVerifyWorkflow(verify_checks),
        )
    )


def _selected_image_contracts(
    resolved_services: tuple[str, ...] | None, repository_root: Path,
) -> tuple[ContainerImageContract, ...]:
    contracts = _container_image_contracts_from_environment(repository_root)
    if resolved_services is None:
        return contracts
    contexts = artifact_contexts(repository_root, resolved_services)
    selected = tuple(contract for contract in contracts if contract.build_context in contexts)
    if any(contract.source == "build" for contract in selected) and "nexus" not in resolved_services:
        raise ValueError("Selected build images require the Nexus registry service.")
    return selected


def _nexus_bootstrap_steps(
    backend: ManagedLxcBackend,
    process_runner: ProcessRunner,
    nexus_admin_password: str,
    ui: PortUI | None,
    progress: PortWorkflowProgress | None,
) -> tuple[ArtifactPrepareStep, ...]:
    nexus_client = LxcNexusHttpClient(backend=backend)
    container_runtime = LxcContainerRuntime(
        backend=backend,
        process_runner=process_runner,
        node_names=tuple(node.name for node in DEFAULT_LXC_PLATFORM_NODES),
    )
    wait_for_nexus_ready = WaitForNexusReady(
        nexus_client=nexus_client,
        max_attempts=60,
        wait_seconds=10,
        progress=progress,
    )
    ensure_nexus_admin_access = EnsureNexusAdminAccess(
        nexus_client=nexus_client,
        container_runtime=container_runtime,
        admin_username="admin",
        admin_password=nexus_admin_password,
        container_name_filter="nexus",
        initial_password_path="/nexus-data/admin.password",
        max_attempts=60,
        wait_seconds=10,
        ui=ui,
        progress=progress,
    )
    nexus_repository_steps = (
        EnsureNexusDockerHostedRepository(
            nexus_client=nexus_client,
            configuration=NexusDockerHostedRepositoryConfiguration(
                repository_name="docker-hosted",
                http_port=5000,
                admin_username="admin",
                admin_password=nexus_admin_password,
            ),
        ),
        EnsureNexusDockerProxyRepository(
            nexus_client=nexus_client,
            configuration=NexusDockerProxyRepositoryConfiguration(
                repository_name=_nexus_docker_hub_proxy_repository_name(),
                http_port=_nexus_docker_hub_proxy_port(),
                remote_url=_nexus_docker_proxy_remote_url(),
                admin_username="admin",
                admin_password=nexus_admin_password,
            ),
        ),
        EnsureNexusMavenProxyRepository(
            nexus_client=nexus_client,
            configuration=NexusMavenProxyRepositoryConfiguration(
                repository_name="maven-central-proxy",
                remote_url="https://repo1.maven.org/maven2/",
                admin_username="admin",
                admin_password=nexus_admin_password,
            ),
        ),
    )
    return (
        wait_for_nexus_ready,
        ensure_nexus_admin_access,
        *nexus_repository_steps,
    )


_BOUNDARY_DEFAULTS = {
    name: globals()[name]
    for name in _BOUNDARY_FUNCTION_NAMES
}
