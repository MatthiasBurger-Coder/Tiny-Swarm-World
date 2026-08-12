"""Platform composition boundary.

Concrete platform service construction lives in this focused
infrastructure module. Runtime compatibility symbols are refreshed before
calls so legacy facade patch points remain effective.
"""

from __future__ import annotations

from .composition_runtime import (
    AsyncLxcNodeCommandRunner,
    ClusterWorkflows,
    CommandWorkflow,
    DEFAULT_LXC_MANAGER_PROXY_PROFILE,
    DEFAULT_SETUP_SERVICE_PROFILE,
    HostPreparationAdapterFactory,
    HostPreparationService,
    LiveConsent,
    LoggerFactory,
    LxcContainerDockerRuntime,
    LxcDockerInstallService,
    LxcNodeProvider,
    LxcProviderPreflightProbe,
    LxcProxyDeviceRuntime,
    LxcProxyDriftRepairService,
    LxcServiceExposureService,
    LxcSwarmBootstrapService,
    NodeProviderConfigYamlRepository,
    NodeProviderSelectionRequest,
    NodeProviderSelectionService,
    Path,
    PlatformDestroyWorkflow,
    PlatformExposeWorkflow,
    PlatformInitWorkflow,
    PlatformReconcileWorkflow,
    PlatformRepairLxcProxyDriftWorkflow,
    PlatformResetWorkflow,
    PlatformServices,
    PlatformVerifyWorkflow,
    PlatformWorkflows,
    PortUI,
    ServiceStackProfile,
    SetupWorkflowPhase,
    SocatManager,
    VerificationEvidenceLocalRepository,
    WslResourceInspector,
    WslSocatExposureAdapter,
    _ProviderSelectedLxcDockerRuntime,
    _ProviderSelectedLxcProxyDeviceRuntime,
    _ProviderSelectedLxcSwarmRuntime,
    _build_method_trace_sink,
    _build_native_linux_host_preparation,
    _build_post_install_preflight_service_for_request,
    _build_preflight_service_for_request,
    _build_workflow_progress_sink,
    _build_wsl_host_preparation,
    _cluster_docker_steps,
    _cluster_swarm_bootstrap_steps,
    _cluster_verify_steps,
    _lxc_docker_apt_mirror_configuration,
    _lxc_docker_registry_mirror_configuration,
    _lxc_manager_node,
    _lxc_proxy_listen_address,
    _new_installation_trace_correlation_id,
    _node_provider_request_from_config,
    _operator_config_float,
    _platform_destroy_steps,
    _platform_expose_steps,
    _platform_init_pre_apply_guard,
    _platform_init_steps,
    _platform_reconcile_steps,
    _platform_repair_lxc_proxy_drift_steps,
    _platform_reset_steps,
    _platform_verify_steps,
    _wsl_lxc_lifecycle_capability_available,
    build_host_environment_detector,
    default_project_paths,
    default_setup_manifest,
    os,
)
from . import composition_runtime as _runtime

_BOUNDARY_FUNCTION_NAMES = frozenset(["build_host_preparation_service","build_platform_services"])
_RUNTIME_SYMBOL_NAMES = frozenset(["AsyncLxcNodeCommandRunner","ClusterWorkflows","CommandWorkflow","DEFAULT_LXC_MANAGER_PROXY_PROFILE","DEFAULT_SETUP_SERVICE_PROFILE","HostPreparationAdapterFactory","HostPreparationService","LiveConsent","LoggerFactory","LxcContainerDockerRuntime","LxcDockerInstallService","LxcNodeProvider","LxcProviderPreflightProbe","LxcProxyDeviceRuntime","LxcProxyDriftRepairService","LxcServiceExposureService","LxcSwarmBootstrapService","NodeProviderConfigYamlRepository","NodeProviderSelectionRequest","NodeProviderSelectionService","Path","PlatformDestroyWorkflow","PlatformExposeWorkflow","PlatformInitWorkflow","PlatformReconcileWorkflow","PlatformRepairLxcProxyDriftWorkflow","PlatformResetWorkflow","PlatformServices","PlatformVerifyWorkflow","PlatformWorkflows","PortUI","ServiceStackProfile","SetupWorkflowPhase","SocatManager","VerificationEvidenceLocalRepository","WslResourceInspector","WslSocatExposureAdapter","_ProviderSelectedLxcDockerRuntime","_ProviderSelectedLxcProxyDeviceRuntime","_ProviderSelectedLxcSwarmRuntime","_build_method_trace_sink","_build_native_linux_host_preparation","_build_post_install_preflight_service_for_request","_build_preflight_service_for_request","_build_workflow_progress_sink","_build_wsl_host_preparation","_cluster_docker_steps","_cluster_swarm_bootstrap_steps","_cluster_verify_steps","_lxc_docker_apt_mirror_configuration","_lxc_docker_registry_mirror_configuration","_lxc_manager_node","_lxc_proxy_listen_address","_new_installation_trace_correlation_id","_node_provider_request_from_config","_operator_config_float","_platform_destroy_steps","_platform_expose_steps","_platform_init_pre_apply_guard","_platform_init_steps","_platform_reconcile_steps","_platform_repair_lxc_proxy_drift_steps","_platform_reset_steps","_platform_verify_steps","_wsl_lxc_lifecycle_capability_available","build_host_environment_detector","default_project_paths","default_setup_manifest","os","build_host_preparation_service","build_platform_services"])


def _refresh_runtime_symbols() -> None:
    for name in _RUNTIME_SYMBOL_NAMES:
        if name not in _BOUNDARY_FUNCTION_NAMES:
            globals()[name] = getattr(_runtime, name)


_refresh_runtime_symbols()


def build_host_preparation_service(
    live_consent: LiveConsent | None = None,
) -> HostPreparationService:
    project_paths = default_project_paths()
    bridge_root = project_paths.repository_root / "tools" / "windows"
    script_path = Path(
        os.getenv("TSW_WINDOWS_BRIDGE_SCRIPT_PATH", str(bridge_root / "tws-wsl-bridge.ps1"))
    )
    config_path = Path(
        os.getenv("TSW_WINDOWS_BRIDGE_CONFIG_PATH", str(bridge_root / "tws-wsl-bridge.config.json"))
    )
    registry_path = Path(
        os.getenv(
            "TSW_WINDOWS_BRIDGE_PORT_REGISTRY_PATH",
            str(project_paths.config_root / "ports.yaml"),
        )
    )
    timeout_seconds = _operator_config_float(
        "TSW_WINDOWS_BRIDGE_TIMEOUT_SECONDS",
        120.0,
        minimum=1.0,
    )
    return HostPreparationService(
        build_host_environment_detector(),
        HostPreparationAdapterFactory(_build_native_linux_host_preparation),
        HostPreparationAdapterFactory(
            lambda: _build_wsl_host_preparation(
                script_path=script_path,
                config_path=config_path,
                registry_path=registry_path,
                timeout_seconds=timeout_seconds,
            )
        ),
        live_consent,
    )

def build_platform_services(
    service_profile: ServiceStackProfile | str = DEFAULT_SETUP_SERVICE_PROFILE,
    live_consent: LiveConsent | None = None,
    node_provider_request: NodeProviderSelectionRequest | None = None,
    ui: PortUI | None = None,
    trace_correlation_id: str | None = None,
    allow_wsl_windows_filesystem: bool = False,
) -> PlatformServices:
    project_paths = default_project_paths()
    node_provider_config_repository = NodeProviderConfigYamlRepository(
        project_paths=project_paths
    )
    provider_config = node_provider_config_repository.load()
    provider_request = node_provider_request or _node_provider_request_from_config(provider_config)
    workflow_progress = _build_workflow_progress_sink(ui)
    method_trace = _build_method_trace_sink(ui)
    trace_correlation_id = trace_correlation_id or _new_installation_trace_correlation_id()

    command_workflow = CommandWorkflow()
    verification_evidence_repository = VerificationEvidenceLocalRepository()
    preflight = _build_preflight_service_for_request(
        service_profile,
        provider_request,
        project_paths=project_paths,
        allow_wsl_windows_filesystem=allow_wsl_windows_filesystem,
    )
    post_install_preflight = _build_post_install_preflight_service_for_request(
        service_profile,
        provider_request,
        project_paths=project_paths,
        allow_wsl_windows_filesystem=allow_wsl_windows_filesystem,
    )
    lxc_runner = AsyncLxcNodeCommandRunner()
    lxc_node_provider = LxcNodeProvider(
        config_repository=node_provider_config_repository,
        runner=lxc_runner,
        allow_live_mutation=False if live_consent is None else live_consent.accepted,
        host_resource_inspector=WslResourceInspector(),
    )
    node_provider_selection = NodeProviderSelectionService(
        LxcProviderPreflightProbe(
            wsl_lxc_capability_available=_wsl_lxc_lifecycle_capability_available,
        ),
        lxc_node_provider,
        lxc_node_provider,
    )
    lxc_docker_runtime = _ProviderSelectedLxcDockerRuntime(
        provider_selection=node_provider_selection,
        provider_request=provider_request,
        runner=lxc_runner,
        allow_live_mutation=False if live_consent is None else live_consent.accepted,
        registry_mirror_configuration=_lxc_docker_registry_mirror_configuration,
        apt_mirror_configuration=_lxc_docker_apt_mirror_configuration,
        docker_runtime_factory=LxcContainerDockerRuntime,
    )
    lxc_docker_install = LxcDockerInstallService(lxc_docker_runtime)
    lxc_docker_verify = LxcDockerInstallService(
        _ProviderSelectedLxcDockerRuntime(
            provider_selection=node_provider_selection,
            provider_request=provider_request,
            runner=lxc_runner,
            allow_live_mutation=False,
            allow_live_inspection=True,
            registry_mirror_configuration=_lxc_docker_registry_mirror_configuration,
            apt_mirror_configuration=_lxc_docker_apt_mirror_configuration,
            docker_runtime_factory=LxcContainerDockerRuntime,
        )
    )
    lxc_swarm_runtime = _ProviderSelectedLxcSwarmRuntime(
        provider_selection=node_provider_selection,
        provider_request=provider_request,
        runner=lxc_runner,
        allow_live_mutation=False if live_consent is None else live_consent.accepted,
        proxy_runtime_factory=LxcProxyDeviceRuntime,
    )
    lxc_swarm_bootstrap = LxcSwarmBootstrapService(
        lxc_swarm_runtime,
        lxc_swarm_runtime,
    )
    lxc_swarm_verify = LxcSwarmBootstrapService(
        _ProviderSelectedLxcSwarmRuntime(
            provider_selection=node_provider_selection,
            provider_request=provider_request,
            runner=lxc_runner,
            allow_live_mutation=False,
            allow_live_inspection=True,
            proxy_runtime_factory=LxcProxyDeviceRuntime,
        ),
        lxc_swarm_runtime,
    )
    lxc_proxy_runtime = _ProviderSelectedLxcProxyDeviceRuntime(
        provider_selection=node_provider_selection,
        provider_request=provider_request,
        runner=lxc_runner,
        allow_live_mutation=False if live_consent is None else live_consent.accepted,
    )
    lxc_service_exposure = LxcServiceExposureService(
        lxc_proxy_runtime,
        gateway_node=_lxc_manager_node(),
        manager_profile_name=DEFAULT_LXC_MANAGER_PROXY_PROFILE,
        setup_manifest=default_setup_manifest(service_profile=service_profile),
        listen_address=_lxc_proxy_listen_address(),
        logger=LoggerFactory.get_logger("LxcServiceExposureService"),
    )
    lxc_service_exposure_verify = LxcServiceExposureService(
        _ProviderSelectedLxcProxyDeviceRuntime(
            provider_selection=node_provider_selection,
            provider_request=provider_request,
            runner=lxc_runner,
            allow_live_mutation=False,
            allow_live_inspection=True,
        ),
        gateway_node=_lxc_manager_node(),
        manager_profile_name=DEFAULT_LXC_MANAGER_PROXY_PROFILE,
        setup_manifest=default_setup_manifest(service_profile=service_profile),
        listen_address=_lxc_proxy_listen_address(),
        logger=LoggerFactory.get_logger("LxcServiceExposureVerifyService"),
    )
    lxc_proxy_drift_repair = LxcProxyDriftRepairService(
        lxc_proxy_runtime,
        gateway_node=_lxc_manager_node(),
        manager_profile_name=DEFAULT_LXC_MANAGER_PROXY_PROFILE,
        setup_manifest=default_setup_manifest(service_profile=service_profile),
        listen_address=_lxc_proxy_listen_address(),
    )
    socat_manager = SocatManager()
    socat_exposure = WslSocatExposureAdapter()
    init_steps = _platform_init_steps(
        provider_request=provider_request,
        node_provider_selection=node_provider_selection,
    )
    workflows = PlatformWorkflows(
        init=PlatformInitWorkflow(
            init_steps,
            verification_evidence_repository=verification_evidence_repository,
            pre_apply_guard=(
                SetupWorkflowPhase(
                    "platform init preflight",
                    lambda: _platform_init_pre_apply_guard(
                        preflight,
                        node_provider_selection,
                        provider_request,
                        live_consent,
                    ),
                    method_trace=method_trace,
                    trace_correlation_id=trace_correlation_id,
                )
                if live_consent is not None
                else None
            ),
            progress=workflow_progress,
            method_trace=method_trace,
            trace_correlation_id=trace_correlation_id,
        ),
        reconcile=PlatformReconcileWorkflow(
            _platform_reconcile_steps(
                provider_request=provider_request,
                node_provider_selection=node_provider_selection,
            ),
            verification_evidence_repository=verification_evidence_repository,
            progress=workflow_progress,
            method_trace=method_trace,
            trace_correlation_id=trace_correlation_id,
        ),
        expose=PlatformExposeWorkflow(
            _platform_expose_steps(
                lxc_service_exposure,
                socat_manager,
                socat_exposure,
                service_profile=ServiceStackProfile(service_profile),
                live_consent=live_consent,
            ),
            verification_evidence_repository=verification_evidence_repository,
            progress=workflow_progress,
            method_trace=method_trace,
            trace_correlation_id=trace_correlation_id,
        ),
        repair_lxc_proxy_drift=PlatformRepairLxcProxyDriftWorkflow(
            _platform_repair_lxc_proxy_drift_steps(lxc_proxy_drift_repair),
            verification_evidence_repository=verification_evidence_repository,
            progress=workflow_progress,
            method_trace=method_trace,
            trace_correlation_id=trace_correlation_id,
        ),
        reset=PlatformResetWorkflow(
            _platform_reset_steps(
                provider_request,
                node_provider_selection,
            ),
            verification_evidence_repository=verification_evidence_repository,
            progress=workflow_progress,
            method_trace=method_trace,
            trace_correlation_id=trace_correlation_id,
        ),
        destroy=PlatformDestroyWorkflow(
            _platform_destroy_steps(
                provider_request,
                node_provider_selection,
            ),
            verification_evidence_repository=verification_evidence_repository,
            progress=workflow_progress,
            method_trace=method_trace,
            trace_correlation_id=trace_correlation_id,
        ),
        verify=PlatformVerifyWorkflow(
            _platform_verify_steps(
                post_install_preflight,
                provider_request=provider_request,
                node_provider_selection=node_provider_selection,
                lxc_service_exposure=lxc_service_exposure_verify,
            ),
            progress=workflow_progress,
            method_trace=method_trace,
            trace_correlation_id=trace_correlation_id,
            verify_retry_attempts=6,
            verify_retry_delay_seconds=10.0,
        ),
        cluster=ClusterWorkflows(
            docker=PlatformInitWorkflow(
                _cluster_docker_steps(lxc_docker_install),
                verification_evidence_repository=verification_evidence_repository,
                progress=workflow_progress,
                method_trace=method_trace,
                trace_correlation_id=trace_correlation_id,
            ),
            swarm_bootstrap=PlatformInitWorkflow(
                _cluster_swarm_bootstrap_steps(lxc_swarm_bootstrap),
                verification_evidence_repository=verification_evidence_repository,
                progress=workflow_progress,
                method_trace=method_trace,
                trace_correlation_id=trace_correlation_id,
            ),
            verify=PlatformVerifyWorkflow(
                _cluster_verify_steps(
                    lxc_docker_verify,
                    lxc_swarm_verify,
                ),
                progress=workflow_progress,
                method_trace=method_trace,
                trace_correlation_id=trace_correlation_id,
                verify_retry_attempts=6,
                verify_retry_delay_seconds=10.0,
            ),
        ),
    )

    return PlatformServices(
        command_workflow=command_workflow,
        lxc_docker_install=lxc_docker_install,
        lxc_proxy_drift_repair=lxc_proxy_drift_repair,
        lxc_service_exposure=lxc_service_exposure,
        lxc_swarm_bootstrap=lxc_swarm_bootstrap,
        preflight=preflight,
        lxc_node_provider=lxc_node_provider,
        node_provider_selection=node_provider_selection,
        socat_manager=socat_manager,
        workflows=workflows,
    )


_BOUNDARY_DEFAULTS = {
    name: globals()[name]
    for name in _BOUNDARY_FUNCTION_NAMES
}
