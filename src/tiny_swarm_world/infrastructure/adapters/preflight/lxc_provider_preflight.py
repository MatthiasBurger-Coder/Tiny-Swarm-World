from __future__ import annotations

import asyncio
import os
import shutil
from collections.abc import Callable, Sequence
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from tiny_swarm_world.application.ports.node_provider import PortNodeProviderReadiness
from tiny_swarm_world.domain.node_provider import (
    ManagedLxcBackend,
    ManagedLxcBackendSelection,
    NodeProviderKind,
    ProviderReadiness,
    ProviderReadinessStatus,
)
from tiny_swarm_world.domain.preflight import (
    HostEnvironmentKind,
    HostEnvironmentReport,
)
from tiny_swarm_world.infrastructure.adapters.preflight.host_preflight_probe import (
    HostPreflightProbe,
)


DEFAULT_LXC_PROVIDER_TIMEOUT_SECONDS = 5.0
COMMON_LXC_EXECUTABLE_DIRECTORIES = (Path("/snap/bin"),)

_BACKEND_CLI = {
    ManagedLxcBackend.INCUS: "incus",
    ManagedLxcBackend.LXD: "lxc",
}
_READINESS_COMMANDS = {
    ManagedLxcBackend.INCUS: (("incus", "version"), ("incus", "info")),
    ManagedLxcBackend.LXD: (("lxc", "version"), ("lxc", "info")),
}


@dataclass(frozen=True)
class LxcProviderProbeResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False


class LxcProviderProbeRunner(Protocol):
    async def run(
        self,
        args: Sequence[str],
        timeout_seconds: float,
    ) -> LxcProviderProbeResult:
        # Protocol declaration; concrete runners probe the selected LXC backend.
        pass


class AsyncLxcProviderProbeRunner:
    async def run(
        self,
        args: Sequence[str],
        timeout_seconds: float,
    ) -> LxcProviderProbeResult:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            with suppress(ProcessLookupError):
                process.kill()
            with suppress(asyncio.TimeoutError):
                await asyncio.wait_for(process.wait(), timeout=1.0)
            return LxcProviderProbeResult(returncode=124, timed_out=True)

        return LxcProviderProbeResult(
            returncode=process.returncode if process.returncode is not None else -1,
            stdout=_safe_process_text(stdout),
            stderr=_safe_process_text(stderr),
        )


class LxcProviderPreflightProbe(PortNodeProviderReadiness):
    def __init__(
        self,
        *,
        host_environment_provider: Callable[[], HostEnvironmentReport] | None = None,
        executable_available: Callable[[str], bool] | None = None,
        runner: LxcProviderProbeRunner | None = None,
        systemd_available: Callable[[], bool] | None = None,
        wsl_lxc_capability_available: Callable[[], bool] | None = None,
        timeout_seconds: float = DEFAULT_LXC_PROVIDER_TIMEOUT_SECONDS,
        executable_fallback_directories: Sequence[Path] = COMMON_LXC_EXECUTABLE_DIRECTORIES,
    ):
        self.host_environment_provider = (
            host_environment_provider or HostPreflightProbe().host_environment_report
        )
        self.executable_available = executable_available or _default_executable_available(
            executable_fallback_directories
        )
        self.runner = runner or AsyncLxcProviderProbeRunner()
        self.systemd_available = systemd_available or _default_systemd_available
        self.wsl_lxc_capability_available = (
            wsl_lxc_capability_available or _default_wsl_lxc_capability_available
        )
        self.timeout_seconds = timeout_seconds

    async def provider_readiness(
        self,
        provider: NodeProviderKind,
        preferred_backend: ManagedLxcBackend | None = None,
    ) -> ProviderReadiness:
        if provider != NodeProviderKind.LXC_NATIVE:
            return ProviderReadiness(
                provider=provider,
                status=ProviderReadinessStatus.UNSUPPORTED,
                remediation=("Use the LXC-native readiness probe only for lxc_native.",),
                evidence={"requested_provider": provider.value},
            )

        host_environment = self.host_environment_provider()
        host_gate = _host_gate(
            host_environment,
            self.systemd_available,
            self.wsl_lxc_capability_available,
        )
        if host_gate is not None:
            return host_gate

        backend_candidates = (
            (preferred_backend,)
            if preferred_backend is not None
            else (ManagedLxcBackend.INCUS, ManagedLxcBackend.LXD)
        )
        available_backends = tuple(
            backend
            for backend in backend_candidates
            if self.executable_available(_BACKEND_CLI[backend])
        )
        if not available_backends:
            return _backend_missing_readiness(host_environment, backend_candidates)

        probe_results: list[_BackendProbeReadiness] = []
        for backend in available_backends:
            probe_results.append(await self._probe_backend(backend, host_environment))

        ready_backends = tuple(result.backend for result in probe_results if result.ready)
        if preferred_backend is None and len(ready_backends) > 1:
            return ProviderReadiness(
                provider=NodeProviderKind.LXC_NATIVE,
                status=ProviderReadinessStatus.BACKEND_AMBIGUOUS,
                backend_selection=ManagedLxcBackendSelection.ambiguous(
                    candidates=ready_backends,
                    remediation=("Set an explicit managed LXC backend preference.",),
                    evidence=_backend_presence_evidence(
                        host_environment,
                        backend_candidates,
                        available_backends,
                    ),
                ),
                remediation=("Both Incus and LXD are usable; choose one explicitly.",),
                evidence={"host_kind": host_environment.environment.value},
            )
        if ready_backends:
            return _ready_readiness(host_environment, ready_backends[0])

        return probe_results[0].readiness

    async def _probe_backend(
        self,
        backend: ManagedLxcBackend,
        host_environment: HostEnvironmentReport,
    ) -> _BackendProbeReadiness:
        for probe_name, args in (
            ("version", _READINESS_COMMANDS[backend][0]),
            ("info", _READINESS_COMMANDS[backend][1]),
        ):
            result = await self.runner.run(args, self.timeout_seconds)
            if result.returncode == 0 and not result.timed_out:
                continue
            return _BackendProbeReadiness(
                backend=backend,
                readiness=_failure_readiness(
                    host_environment,
                    backend,
                    probe_name,
                    result,
                ),
            )
        return _BackendProbeReadiness(
            backend=backend,
            readiness=_ready_readiness(host_environment, backend),
        )


@dataclass(frozen=True)
class _BackendProbeReadiness:
    backend: ManagedLxcBackend
    readiness: ProviderReadiness

    @property
    def ready(self) -> bool:
        return self.readiness.ready


def _host_gate(
    host_environment: HostEnvironmentReport,
    systemd_available: Callable[[], bool],
    wsl_lxc_capability_available: Callable[[], bool],
) -> ProviderReadiness | None:
    if host_environment.environment == HostEnvironmentKind.WSL2:
        if not systemd_available():
            return _host_blocked_readiness(
                ProviderReadinessStatus.SYSTEMD_UNAVAILABLE,
                host_environment,
                "Enable systemd in WSL2 before running LXD or Incus daemon checks.",
                {"systemd": "absent", "wsl_generation": "2"},
            )
        if not wsl_lxc_capability_available():
            return _host_blocked_readiness(
                ProviderReadinessStatus.WSL_UNSUPPORTED,
                host_environment,
                "Verify WSL2 managed LXC capability before live setup.",
                {"systemd": "present", "wsl_generation": "2", "wsl_capability": "unsupported"},
            )
        return None
    if host_environment.environment == HostEnvironmentKind.NATIVE_LINUX:
        return None
    status = (
        ProviderReadinessStatus.WSL_UNSUPPORTED
        if host_environment.environment == HostEnvironmentKind.WSL1_UNSUPPORTED
        else ProviderReadinessStatus.HOST_UNSUPPORTED
    )
    return _host_blocked_readiness(
        status,
        host_environment,
        "Run provider readiness from native Linux or verified WSL2.",
        {},
    )


def _host_blocked_readiness(
    status: ProviderReadinessStatus,
    host_environment: HostEnvironmentReport,
    remediation: str,
    extra_evidence: dict[str, str],
) -> ProviderReadiness:
    evidence = {"host_kind": host_environment.environment.value, **extra_evidence}
    return ProviderReadiness(
        provider=NodeProviderKind.LXC_NATIVE,
        status=status,
        backend_selection=ManagedLxcBackendSelection.unsupported(
            remediation=(remediation,),
            evidence=evidence,
        ),
        remediation=(remediation,),
        evidence=evidence,
    )


def _backend_missing_readiness(
    host_environment: HostEnvironmentReport,
    backend_candidates: tuple[ManagedLxcBackend, ...],
) -> ProviderReadiness:
    return ProviderReadiness(
        provider=NodeProviderKind.LXC_NATIVE,
        status=ProviderReadinessStatus.BACKEND_MISSING,
        backend_selection=ManagedLxcBackendSelection.missing(
            remediation=("Install Incus or LXD and make the selected CLI available.",),
            evidence=_backend_presence_evidence(host_environment, backend_candidates, ()),
        ),
        remediation=("Install Incus or LXD and make the selected CLI available.",),
        evidence={"host_kind": host_environment.environment.value},
    )


def _ready_readiness(
    host_environment: HostEnvironmentReport,
    backend: ManagedLxcBackend,
) -> ProviderReadiness:
    evidence = {
        "host_kind": host_environment.environment.value,
        "backend": backend.value,
        "version_probe": "passed",
        "info_probe": "passed",
    }
    return ProviderReadiness(
        provider=NodeProviderKind.LXC_NATIVE,
        status=ProviderReadinessStatus.READY,
        backend_selection=ManagedLxcBackendSelection.for_backend(
            backend,
            evidence=evidence,
        ),
        evidence=evidence,
    )


def _failure_readiness(
    host_environment: HostEnvironmentReport,
    backend: ManagedLxcBackend,
    probe_name: str,
    result: LxcProviderProbeResult,
) -> ProviderReadiness:
    status = _failure_status(result)
    remediation = _failure_remediation(status, backend)
    evidence = {
        "host_kind": host_environment.environment.value,
        "backend": backend.value,
        "probe": probe_name,
        "return_code": str(result.returncode),
        "classification": status.value,
    }
    if result.timed_out:
        evidence["classification_source"] = "timeout"
    return ProviderReadiness(
        provider=NodeProviderKind.LXC_NATIVE,
        status=status,
        backend_selection=ManagedLxcBackendSelection.for_backend(
            backend,
            remediation=(remediation,),
            evidence=evidence,
        ),
        remediation=(remediation,),
        evidence=evidence,
    )


def _failure_status(result: LxcProviderProbeResult) -> ProviderReadinessStatus:
    if result.timed_out:
        return ProviderReadinessStatus.TIMEOUT
    output = f"{result.stdout}\n{result.stderr}".casefold()
    if "permission denied" in output or "access denied" in output or "not authorized" in output:
        return ProviderReadinessStatus.PERMISSION_DENIED
    if (
        "cannot connect" in output
        or "connection refused" in output
        or "daemon" in output
        or "socket" in output
        or "not running" in output
    ):
        return ProviderReadinessStatus.DAEMON_UNAVAILABLE
    return ProviderReadinessStatus.UNKNOWN_FAILURE


def _failure_remediation(
    status: ProviderReadinessStatus,
    backend: ManagedLxcBackend,
) -> str:
    backend_name = backend.value
    if status == ProviderReadinessStatus.TIMEOUT:
        return f"Verify the {backend_name} daemon responds to read-only commands."
    if status == ProviderReadinessStatus.PERMISSION_DENIED:
        return f"Grant the current Linux user access to the {backend_name} provider daemon."
    if status == ProviderReadinessStatus.DAEMON_UNAVAILABLE:
        return f"Start or repair the {backend_name} provider daemon before live setup."
    return f"Repair {backend_name} provider readiness before live setup."


def _backend_presence_evidence(
    host_environment: HostEnvironmentReport,
    candidates: tuple[ManagedLxcBackend, ...],
    available_backends: tuple[ManagedLxcBackend, ...],
) -> dict[str, str]:
    available = set(available_backends)
    evidence = {"host_kind": host_environment.environment.value}
    for backend in candidates:
        evidence[f"{backend.value}_cli"] = "present" if backend in available else "absent"
    return evidence


def _default_executable_available(
    fallback_directories: Sequence[Path],
) -> Callable[[str], bool]:
    def executable_available(name: str) -> bool:
        return shutil.which(name, path=_executable_search_path(fallback_directories)) is not None

    return executable_available


def _default_systemd_available() -> bool:
    return Path("/run/systemd/system").exists() or _read_os_file(
        Path("/proc/1/comm")
    ).strip() == "systemd"


def _default_wsl_lxc_capability_available() -> bool:
    return True


def _executable_search_path(fallback_directories: Sequence[Path]) -> str:
    entries = [entry for entry in os.environ.get("PATH", "").split(os.pathsep) if entry]
    present = set(entries)
    for directory in fallback_directories:
        directory_text = str(directory)
        if directory.is_dir() and directory_text not in present:
            entries.append(directory_text)
            present.add(directory_text)
    return os.pathsep.join(entries)


def _read_os_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _safe_process_text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return value
