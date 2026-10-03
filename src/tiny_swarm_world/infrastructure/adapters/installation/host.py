"""Host responsibilities for the live installation boundary."""

from __future__ import annotations
from tiny_swarm_world.application.ports.installation import InstallerOptions
from collections.abc import Callable, Mapping
from pathlib import Path
from tiny_swarm_world.domain.host_environment import HostEnvironmentKind
from tiny_swarm_world.domain.project_filesystem import (
    ProjectFilesystemAssessment,
    ProjectFilesystemDecision,
    assess_project_filesystem,
)
from tiny_swarm_world.application.ports.repositories.port_project_filesystem_evidence_repository import (
    ProjectFilesystemEvidenceError,
)
from tiny_swarm_world.infrastructure.adapters.host import (
    HostEnvironmentDetector,
    ProjectFilesystemInspector,
)
from tiny_swarm_world.infrastructure.adapters.repositories.project_filesystem_evidence_local_repository import (
    ProjectFilesystemEvidenceLocalRepository,
)
from tiny_swarm_world.application.ports.installation import (
    HostRuntime,
    InstallerError,
    WINDOWS_EXPOSURE_ENVIRONMENT,
    WINDOWS_WSL_BRIDGE_MAX_AGE_SECONDS,
    WINDOWS_WSL_BRIDGE_TEST_STATE_ENVIRONMENT,
    WindowsWslBridgeGuardResult,
)


def _require_repository(cwd: Path) -> None:
    if not (cwd / "src" / "tiny_swarm_world").is_dir():
        raise InstallerError(
            "Run this script from the Tiny Swarm World repository root."
        )


def detect_host_runtime(
    env: Mapping[str, str],
    *,
    os_root: Path = Path("/"),
    platform_system: Callable[[], str] | None = None,
) -> HostRuntime:
    test_runtime = env.get("TSW_INSTALL_TEST_HOST_RUNTIME")
    if env.get("TSW_INSTALL_TEST_MODE") == "1" and test_runtime in {
        "wsl2",
        "native_linux",
    }:
        return HostRuntime(test_runtime, "test_override")
    report = HostEnvironmentDetector(
        os_root=os_root,
        environment=env,
        platform_system=platform_system,
    ).detect()
    if report.environment in {
        HostEnvironmentKind.NATIVE_LINUX,
        HostEnvironmentKind.WSL2,
    }:
        return HostRuntime(
            report.environment.value,
            str(report.evidence.get("classification", report.environment.value)),
            report,
        )
    remediation = " ".join(report.remediation) or "Use native Linux or WSL2."
    raise InstallerError(
        f"Unsupported host environment '{report.environment.value}'. {remediation}"
    )


def authorize_project_filesystem(
    host_runtime: HostRuntime,
    cwd: Path,
    *,
    allow_wsl_windows_filesystem: bool,
    env: Mapping[str, str],
) -> ProjectFilesystemAssessment:
    host_environment = (
        host_runtime.environment_report.environment
        if host_runtime.environment_report is not None
        else HostEnvironmentKind(host_runtime.name)
    )
    inspector = ProjectFilesystemInspector()
    inspection = inspector.inspect(cwd.as_posix(), host_environment)
    assessment = assess_project_filesystem(
        host_environment,
        inspection,
        allow_wsl_windows_filesystem=allow_wsl_windows_filesystem,
    )
    if assessment.decision is ProjectFilesystemDecision.ALLOWED_BY_OVERRIDE:
        repository = ProjectFilesystemEvidenceLocalRepository.from_environment(
            env,
            target_inspector=inspector,
        )
        recorded = assessment.mark_evidence_recorded()
        try:
            repository.write(recorded)
        except ProjectFilesystemEvidenceError as error:
            raise InstallerError(
                "The WSL filesystem override could not be recorded in protected "
                "Linux-native owner-only evidence."
            ) from error
        assessment = recorded
    if assessment.blocked:
        remediation = " ".join(assessment.remediation)
        raise InstallerError(
            f"Project filesystem blocks live installation. {remediation}"
        )
    return assessment


def _windows_wsl_bridge_guard(
    host_runtime: HostRuntime,
    env: Mapping[str, str],
    cwd: Path,
) -> WindowsWslBridgeGuardResult:
    from tiny_swarm_world.infrastructure.adapters.preflight.windows_wsl_bridge_state import (
        configured_windows_wsl_bridge_state_path,
    )

    configured_state_path = configured_windows_wsl_bridge_state_path(env)
    test_state_path = env.get(WINDOWS_WSL_BRIDGE_TEST_STATE_ENVIRONMENT, "").strip()
    if env.get("TSW_INSTALL_TEST_MODE") == "1" and test_state_path:
        configured_state_path = Path(test_state_path)
    state_path = (
        configured_state_path
        if configured_state_path.is_absolute()
        else cwd / configured_state_path
    )
    expected_ports = _windows_wsl_bridge_expected_ports(
        cwd,
        infra_root=Path(env["TSW_INFRA_ROOT"]) if env.get("TSW_INFRA_ROOT") else None,
    )
    if host_runtime.name != "wsl2":
        return WindowsWslBridgeGuardResult(
            True, "not_wsl2", state_path, expected_ports=expected_ports
        )
    if not _windows_exposure_required(env):
        return WindowsWslBridgeGuardResult(
            True,
            "windows_exposure_disabled",
            state_path,
            expected_ports=expected_ports,
        )
    if not state_path.exists():
        return WindowsWslBridgeGuardResult(
            False,
            "state_missing",
            state_path,
            expected_ports=expected_ports,
            missing_ports=expected_ports,
        )
    from tiny_swarm_world.infrastructure.adapters.preflight.windows_wsl_bridge_state import (
        current_wsl_ipv4,
        windows_wsl_bridge_status,
    )

    status = windows_wsl_bridge_status(
        cwd,
        expected_ports,
        state_path=configured_state_path,
        max_age_seconds=WINDOWS_WSL_BRIDGE_MAX_AGE_SECONDS,
        current_wsl_ipv4=current_wsl_ipv4,
    )
    return WindowsWslBridgeGuardResult(
        status.prepared,
        status.reason,
        state_path,
        current_wsl_ip=status.current_wsl_ip,
        state_wsl_ip=status.state_wsl_ip,
        expected_ports=status.expected_ports,
        mapped_ports=status.mapped_ports,
        missing_ports=status.missing_ports,
    )


def _windows_exposure_required(env: Mapping[str, str]) -> bool:
    value = env.get(WINDOWS_EXPOSURE_ENVIRONMENT, "").strip().casefold()
    return value not in {"0", "false", "no", "off", "disabled"}


def _windows_wsl_bridge_expected_ports(
    cwd: Path, *, infra_root: Path | None = None
) -> tuple[int, ...]:
    from tiny_swarm_world.infrastructure.adapters.repositories.port_registry_yaml_repository import (
        PortRegistryYamlRepository,
    )

    registry_path = (infra_root or cwd / "infra") / "config" / "ports.yaml"
    try:
        registry = PortRegistryYamlRepository(registry_path).load()
    except ValueError:
        raise InstallerError("Port registry configuration is invalid.") from None
    return tuple(
        sorted(
            {
                mapping.external_port
                for mapping in registry.mappings
                if mapping.protocol == "tcp" and mapping.external_port is not None
            }
        )
    )


class HostPreparationAdapter:
    def require_repository(self, cwd: Path) -> None:
        return _require_repository(cwd)

    def detect(
        self,
        env: Mapping[str, str],
        *,
        os_root: Path = Path("/"),
        platform_system: Callable[[], str] | None = None,
    ) -> HostRuntime:
        return (
            detect_host_runtime(env)
            if os_root == Path("/") and platform_system is None
            else detect_host_runtime(
                env, os_root=os_root, platform_system=platform_system
            )
        )

    def authorize(
        self,
        host_runtime: HostRuntime,
        cwd: Path,
        *,
        allow_wsl_windows_filesystem: bool,
        env: Mapping[str, str],
    ) -> ProjectFilesystemAssessment:
        return authorize_project_filesystem(
            host_runtime,
            cwd,
            allow_wsl_windows_filesystem=allow_wsl_windows_filesystem,
            env=env,
        )

    def bridge(
        self, host_runtime: HostRuntime, env: Mapping[str, str], cwd: Path
    ) -> WindowsWslBridgeGuardResult:
        return _windows_wsl_bridge_guard(host_runtime, env, cwd)

    def validate_native(
        self, options: InstallerOptions, env: Mapping[str, str], cwd: Path
    ) -> None:
        from tiny_swarm_world.infrastructure.composition_native_preparation import (
            build_native_preparation_service,
        )
        from tiny_swarm_world.infrastructure.adapters.installation.process import (
            _python_imports_available,
        )
        import sys

        try:
            plan = build_native_preparation_service(
                cwd, service_profile=options.service_profile
            ).plan()
        except (OSError, RuntimeError, ValueError) as error:
            raise InstallerError("Native host preparation inventory failed.") from error
        if plan.failures:
            raise InstallerError(
                "Native host preflight failed: " + " ".join(plan.failures)
            )
        if plan.missing_packages:
            raise InstallerError(
                "Native host packages are missing: "
                + ", ".join(plan.missing_packages)
                + ". Run ./prepare_linux.sh separately, then retry ./install.sh."
            )
        if not _python_imports_available(sys.executable, env):
            raise InstallerError(
                "Native Python dependencies are missing. Run ./prepare_linux.sh separately, then retry ./install.sh."
            )
