"""Dependency-light installation contracts and values, usable before venv preparation."""

from __future__ import annotations
from collections.abc import Callable, Mapping, Sequence
from tiny_swarm_world.domain.project_filesystem import ProjectFilesystemAssessment
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from tiny_swarm_world.domain.host_environment import HostEnvironmentReport
from contextlib import AbstractContextManager

RESET_CONFIRMATION = "RESET_TINY_SWARM_PLATFORM"

_RESET_RUN_LOG_FILE = "reset-run.log"

_SETUP_RUN_LOG_FILE = "setup-run.log"

DEFAULT_SERVICE_PROFILE = "service-access"

DEFAULT_SECRET_ENV_FILE = ".tiny-swarm-world/local/live-installation.env"

DEFAULT_NATIVE_LINUX_VENV = ".tiny-swarm-world/install-venv"

DEFAULT_SECRET_MANIFEST_PATH = Path("infra/config/secrets/infisical-secrets.yaml")

TRAEFIK_GUI_USERS_HTPASSWD_ENVIRONMENT = "TSW_TRAEFIK_GUI_USERS_HTPASSWD"

INSTALLER_SUBPROCESS_TIMEOUT_ENVIRONMENT = "TSW_INSTALL_SUBPROCESS_TIMEOUT_SECONDS"

DEFAULT_INSTALLER_SUBPROCESS_TIMEOUT_SECONDS = 900.0

DEFAULT_INSTALLER_PROBE_TIMEOUT_SECONDS = 10.0

WINDOWS_WSL_BRIDGE_MAX_AGE_SECONDS = 5 * 60

WINDOWS_EXPOSURE_ENVIRONMENT = "TSW_WINDOWS_EXPOSURE"

WINDOWS_WSL_BRIDGE_TEST_STATE_ENVIRONMENT = (
    "TSW_INSTALL_TEST_WINDOWS_WSL_BRIDGE_STATE_PATH"
)


@dataclass(frozen=True)
class InstallerOptions:
    service_profile: str
    confirm_reset: bool
    non_interactive_live_approval: bool
    headless: bool
    allow_wsl_windows_filesystem: bool
    native_reconcile: bool = False
    preflight_only: bool = False
    dry_run: bool = False


@dataclass(frozen=True)
class InstallerPaths:
    secret_env_file: Path
    native_linux_venv: Path


@dataclass(frozen=True)
class _GitProbeResult:
    inside_worktree: bool
    path_ignored: bool
    status: str


@dataclass(frozen=True)
class _EvidenceProbeSnapshot:
    git_branch: str
    git_head: str
    platform_system: str
    kernel_release: str
    proc_osrelease: str


@dataclass(frozen=True)
class _InstallRunContext:
    run_id: str
    service_profile: str
    secret_env_file: Path
    checked_secret_keys: tuple[str, ...]
    host_runtime: HostRuntime
    live_execution_mode: str
    live_approval_source: str
    terminal_recording_mode: str
    cwd: Path
    env: Mapping[str, str]
    git_probe: _GitProbeResult
    evidence_probes: _EvidenceProbeSnapshot
    native_reconcile: bool


@dataclass(frozen=True)
class HostRuntime:
    name: str
    detection_source: str
    environment_report: HostEnvironmentReport | None = None


@dataclass(frozen=True)
class InstallerSecretEntry:
    key: str
    source: str
    required: bool
    type: str = ""


@dataclass(frozen=True)
class WindowsWslBridgeGuardResult:
    passed: bool
    reason: str
    state_path: Path
    current_wsl_ip: str = ""
    state_wsl_ip: str = ""
    expected_ports: tuple[int, ...] = ()
    mapped_ports: tuple[int, ...] = ()
    missing_ports: tuple[int, ...] = ()


class InstallReporter(Protocol):
    def report(self, event: object) -> None: ...


@dataclass(frozen=True)
class _FallbackInstallEvent:
    event_type: str
    status: str
    step: str
    target: str = "host"
    message: str = ""
    reason: str | None = None
    evidence_path: Path | None = None
    suggested_commands: Sequence[str] = ()
    duration_seconds: float | None = None
    sequence: int | None = None
    total: int | None = None


class InstallerError(RuntimeError):
    pass


class HostPreparation(Protocol):
    def require_repository(self, cwd: Path) -> None: ...

    def detect(
        self,
        env: Mapping[str, str],
        *,
        os_root: Path = Path("/"),
        platform_system: Callable[[], str] | None = None,
    ) -> HostRuntime: ...

    def authorize(
        self,
        host_runtime: HostRuntime,
        cwd: Path,
        *,
        allow_wsl_windows_filesystem: bool,
        env: Mapping[str, str],
    ) -> ProjectFilesystemAssessment: ...

    def bridge(
        self, host_runtime: HostRuntime, env: Mapping[str, str], cwd: Path
    ) -> WindowsWslBridgeGuardResult: ...

    def validate_native(
        self, options: InstallerOptions, env: Mapping[str, str], cwd: Path
    ) -> None: ...


class ConfigurationPreparation(Protocol):
    def paths(self, env: Mapping[str, str], cwd: Path) -> InstallerPaths: ...

    def snapshot(
        self,
        options: InstallerOptions,
        env: Mapping[str, str],
        cwd: Path,
        host_runtime: HostRuntime,
    ) -> AbstractContextManager[dict[str, str]]: ...

    def validate_read_only(
        self,
        options: InstallerOptions,
        env: Mapping[str, str],
        cwd: Path,
        host_runtime: HostRuntime,
    ) -> None: ...


class PhaseRunner(Protocol):
    def ensure_python(
        self, host_runtime: HostRuntime, paths: InstallerPaths, env: Mapping[str, str]
    ) -> str: ...

    def phase(
        self,
        name: str,
        command: str,
        log_file: Path,
        options: InstallerOptions,
        env: Mapping[str, str],
        cwd: Path,
        reporter: InstallReporter | None = None,
        *,
        sequence: int | None = None,
        total: int | None = None,
    ) -> int: ...

    def current_python(self) -> str: ...

    def recorder_available(self) -> bool: ...

    def command(
        self,
        python_bin: str,
        phase: str,
        options: InstallerOptions,
        approval_argument: str,
    ) -> str: ...


class InstallationEvidence(Protocol):
    def git_probe(self, cwd: Path, path: str) -> _GitProbeResult: ...

    def directory(
        self,
        env: Mapping[str, str],
        *,
        cwd: Path,
        host_runtime: HostRuntime,
        run_id: str,
    ) -> Path: ...

    def probes(
        self, cwd: Path, git_probe: _GitProbeResult
    ) -> _EvidenceProbeSnapshot: ...

    def write_context(
        self, evidence_dir: Path, *, context: _InstallRunContext
    ) -> None: ...

    def append(
        self, evidence_dir: Path, values: Mapping[str, str], *, replace: bool = False
    ) -> None: ...

    def bridge_context(self, guard: WindowsWslBridgeGuardResult) -> dict[str, str]: ...

    def timestamp(self) -> str: ...

    def write(self, path: Path, value: str) -> None: ...

    def run_id(self) -> str: ...

    def path(self, evidence_dir: Path, name: str) -> Path: ...


class InstallationPresentation(Protocol):
    def reporter(self) -> InstallReporter: ...

    def approval(self, options: InstallerOptions) -> tuple[str, str, str]: ...

    def plan(
        self, cwd: Path, options: InstallerOptions, evidence_dir: Path
    ) -> None: ...

    def event(
        self,
        event_type: str,
        status: str,
        step: str,
        *,
        target: str = "host",
        message: str = "",
        reason: str | None = None,
        evidence_path: Path | None = None,
        suggested_commands: Sequence[str] = (),
        sequence: int | None = None,
        total: int | None = None,
    ) -> object: ...

    def confirm_reset(self, options: InstallerOptions) -> None: ...

    def bridge_commands(self, reason: str) -> tuple[str, ...]: ...

    def bridge_failure(
        self, guard: WindowsWslBridgeGuardResult, evidence_dir: Path
    ) -> None: ...

    def tail(self, path: Path, title: str) -> None: ...

    def reset_guidance(self, path: Path) -> None: ...

    def setup_guidance(self, path: Path) -> None: ...

    def message(self, message: str, *, failed: bool = False) -> None: ...

    def completion(
        self, exit_code: int, evidence_dir: Path, *, failed: bool
    ) -> None: ...


class CredentialsPreparation(Protocol):
    def prepare(
        self, options: InstallerOptions, env: Mapping[str, str], paths: InstallerPaths
    ) -> tuple[dict[str, str], tuple[InstallerSecretEntry, ...]]: ...
