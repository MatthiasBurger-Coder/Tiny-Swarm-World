from __future__ import annotations

import socket
import subprocess
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from pathlib import Path
from urllib.parse import urlparse

from tiny_swarm_world.application.ports.preflight import PortLiveReadiness
from tiny_swarm_world.domain.node_provider import ManagedLxcBackend
from tiny_swarm_world.domain.preflight import (
    ARTIFACT_READINESS_TARGETS,
    ReadinessCheckResult,
    ReadinessProbeRequest,
    ReadinessStatus,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc.command.backend_cli import (
    backend_cli,
)


(
    MANAGER_DOCKER_TARGET,
    REGISTRY_ENDPOINT_TARGET,
    NEXUS_ENDPOINT_TARGET,
    NEXUS_REPOSITORIES_TARGET,
    MANAGER_STORAGE_TARGET,
    BUILD_INPUTS_TARGET,
    PUBLIC_PULL_TARGET,
) = ARTIFACT_READINESS_TARGETS

ReadinessProbe = Callable[[ReadinessProbeRequest], ReadinessCheckResult]


class BoundedArtifactReadinessAdapter(PortLiveReadiness):
    """Dispatch bounded, read-only artifact readiness probes by stable target ID."""

    def __init__(
        self,
        probes: Mapping[str, ReadinessProbe],
    ) -> None:
        unknown_targets = set(probes).difference(ARTIFACT_READINESS_TARGETS)
        if unknown_targets:
            raise ValueError("artifact readiness contains an unknown target")
        missing_targets = set(ARTIFACT_READINESS_TARGETS).difference(probes)
        if missing_targets:
            raise ValueError("artifact readiness is missing a required target")
        self._probes = dict(probes)

    def check(self, request: ReadinessProbeRequest) -> ReadinessCheckResult:
        probe = self._probes.get(request.target_id)
        if probe is None:
            return _result(
                request,
                ReadinessStatus.UNKNOWN,
                "The requested readiness observation is not configured.",
                "Configure the phase-local readiness adapter before mutation.",
            )
        try:
            result = probe(request)
        except (TimeoutError, socket.timeout, subprocess.TimeoutExpired):
            return _result(
                request,
                ReadinessStatus.TIMED_OUT,
                "The bounded readiness observation timed out.",
                "Retry the bounded observation after the prerequisite is available.",
            )
        except (ConnectionError, OSError):
            return _result(
                request,
                ReadinessStatus.UNAVAILABLE,
                "The readiness target was unavailable.",
                "Restore the prerequisite endpoint or runtime and retry.",
            )
        except Exception:
            return _result(
                request,
                ReadinessStatus.UNKNOWN,
                "The readiness observation could not be classified safely.",
                "Inspect the phase-local diagnostic evidence before retrying.",
            )
        if not isinstance(result, ReadinessCheckResult):
            return _result(
                request,
                ReadinessStatus.UNKNOWN,
                "The readiness adapter returned no typed result.",
                "Return a typed readiness result before artifact mutation.",
            )
        if result.target_id != request.target_id:
            return _result(
                request,
                ReadinessStatus.UNKNOWN,
                "The readiness adapter returned an invalid target identity.",
                "Align the adapter target with the requested phase-local check.",
            )
        return result


class HttpEndpointReadinessProbe:
    """Bounded HTTP reachability probe that never stores response content."""

    def __init__(
        self,
        endpoint: str,
        *,
        opener: Callable[..., object] | None = None,
        probe_kind: str = "endpoint",
    ) -> None:
        parsed_endpoint = urlparse(endpoint)
        if parsed_endpoint.scheme not in {"http", "https"}:
            raise ValueError("readiness endpoint must use http or https")
        if parsed_endpoint.username or parsed_endpoint.password:
            raise ValueError("readiness endpoint must not contain credentials")
        self.endpoint = endpoint
        self.opener = opener or urllib.request.urlopen
        self.probe_kind = probe_kind

    def __call__(self, request: ReadinessProbeRequest) -> ReadinessCheckResult:
        try:
            response = self.opener(self.endpoint, timeout=request.timeout_seconds)
            status = _response_status(response)
            close = getattr(response, "close", None)
            if callable(close):
                close()
        except urllib.error.HTTPError as exc:
            status = exc.code
        if 200 <= status < 500:
            return _result(
                request,
                ReadinessStatus.READY,
                "The bounded endpoint reachability check passed.",
                "No remediation required.",
                evidence={"probe_kind": self.probe_kind, "http_status": str(status)},
            )
        return _result(
            request,
            ReadinessStatus.FAILED,
            "The bounded endpoint returned a non-ready status.",
            "Restore the endpoint readiness before artifact mutation.",
            evidence={"probe_kind": self.probe_kind, "http_status": str(status)},
        )


class DockerManagerReadinessProbe:
    """Read-only manager Docker probe with a bounded command timeout."""

    def __init__(self, runner: Callable[[float], int] | None = None) -> None:
        self.runner = runner or _run_docker_info

    def __call__(self, request: ReadinessProbeRequest) -> ReadinessCheckResult:
        returncode = self.runner(request.timeout_seconds)
        status = ReadinessStatus.READY if returncode == 0 else ReadinessStatus.FAILED
        return _result(
            request,
            status,
            "Manager Docker readiness was observed." if status is ReadinessStatus.READY else "Manager Docker readiness failed.",
            "No remediation required." if status is ReadinessStatus.READY else "Restore manager Docker readiness before artifact mutation.",
            evidence={"probe_kind": "docker_info"},
        )


class UnavailableArtifactReadinessProbe:
    """Fail-closed probe used when the managed execution backend is unresolved."""

    def __init__(self, *, probe_kind: str) -> None:
        self.probe_kind = probe_kind

    def __call__(self, request: ReadinessProbeRequest) -> ReadinessCheckResult:
        return _result(
            request,
            ReadinessStatus.UNAVAILABLE,
            "The managed readiness execution backend is unavailable.",
            "Resolve exactly one managed LXC backend before artifact mutation.",
            evidence={"probe_kind": self.probe_kind},
        )


class ManagedLxcDockerManagerReadinessProbe:
    """Read-only Docker probe executed inside the managed manager container."""

    def __init__(
        self,
        backend: ManagedLxcBackend,
        *,
        node_name: str = "swarm-manager",
        runner: Callable[[tuple[str, ...], float], int] | None = None,
    ) -> None:
        self.backend = backend
        self.node_name = node_name
        self.runner = runner or self._run

    def __call__(self, request: ReadinessProbeRequest) -> ReadinessCheckResult:
        returncode = self.runner(
            ("docker", "info", "--format", "{{.ServerVersion}}"),
            request.timeout_seconds,
        )
        status = ReadinessStatus.READY if returncode == 0 else ReadinessStatus.FAILED
        return _result(
            request,
            status,
            "Managed manager Docker readiness was observed."
            if status is ReadinessStatus.READY
            else "Managed manager Docker readiness failed.",
            "No remediation required."
            if status is ReadinessStatus.READY
            else "Restore manager Docker readiness before artifact mutation.",
            evidence={"probe_kind": "managed_lxc_docker_info"},
        )

    def _run(self, command: tuple[str, ...], timeout_seconds: float) -> int:
        return _run_managed_lxc_command(
            self.backend,
            self.node_name,
            command,
            timeout_seconds,
        )


class LocalDirectoryReadinessProbe:
    """Read-only directory probe for local build or storage prerequisites."""

    def __init__(self, path: Path, *, probe_kind: str) -> None:
        self.path = path
        self.probe_kind = probe_kind

    def __call__(self, request: ReadinessProbeRequest) -> ReadinessCheckResult:
        ready = self.path.is_dir()
        return _result(
            request,
            ReadinessStatus.READY if ready else ReadinessStatus.FAILED,
            "The bounded local prerequisite check passed."
            if ready
            else "The bounded local prerequisite check failed.",
            "No remediation required."
            if ready
            else "Restore the required local directory before artifact mutation.",
            evidence={"probe_kind": self.probe_kind},
        )


class ManagedLxcDirectoryReadinessProbe:
    """Read-only directory probe executed inside a managed manager container."""

    def __init__(
        self,
        backend: ManagedLxcBackend,
        path: str,
        *,
        node_name: str = "swarm-manager",
        runner: Callable[[tuple[str, ...], float], int] | None = None,
    ) -> None:
        self.backend = backend
        self.path = path
        self.node_name = node_name
        self.runner = runner or self._run

    def __call__(self, request: ReadinessProbeRequest) -> ReadinessCheckResult:
        returncode = self.runner(("test", "-d", self.path), request.timeout_seconds)
        status = ReadinessStatus.READY if returncode == 0 else ReadinessStatus.FAILED
        return _result(
            request,
            status,
            "The bounded managed directory check passed."
            if status is ReadinessStatus.READY
            else "The bounded managed directory check failed.",
            "No remediation required."
            if status is ReadinessStatus.READY
            else "Restore the required manager directory before artifact mutation.",
            evidence={"probe_kind": "managed_lxc_directory"},
        )

    def _run(self, command: tuple[str, ...], timeout_seconds: float) -> int:
        return _run_managed_lxc_command(
            self.backend,
            self.node_name,
            command,
            timeout_seconds,
        )


def _run_managed_lxc_command(
    backend: ManagedLxcBackend,
    node_name: str,
    command: tuple[str, ...],
    timeout_seconds: float,
) -> int:
    completed = subprocess.run(
        (backend_cli(backend), "exec", node_name, "--", *command),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        shell=False,
        timeout=timeout_seconds,
    )
    return completed.returncode


def _response_status(response: object) -> int:
    status = getattr(response, "status", None)
    if status is None:
        get_code = getattr(response, "getcode", None)
        if not callable(get_code):
            raise ValueError("response status unavailable")
        status = get_code()
    return int(status)


def _run_docker_info(timeout_seconds: float) -> int:
    completed = subprocess.run(
        ("docker", "info", "--format", "{{.ServerVersion}}"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        shell=False,
        timeout=timeout_seconds,
    )
    return completed.returncode


def _result(
    request: ReadinessProbeRequest,
    status: ReadinessStatus,
    message: str,
    remediation: str,
    *,
    evidence: Mapping[str, str] | None = None,
) -> ReadinessCheckResult:
    return ReadinessCheckResult(
        target_id=request.target_id,
        status=status,
        message=message,
        remediation=remediation,
        evidence={"evidence_scope": "live", **(dict(evidence) if evidence else {})},
    )
