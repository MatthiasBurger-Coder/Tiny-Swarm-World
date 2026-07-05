from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import socket
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from tiny_swarm_world.application.ports.preflight import PortHostPreflightProbe
from tiny_swarm_world.domain.preflight import (
    HostEnvironmentKind,
    HostEnvironmentReport,
    SetupPath,
    WindowsWslBridgeStatus,
)
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths, default_project_paths


SECRET_TOKEN_PATTERN = re.compile(r"\w[\w-]{2,}", re.ASCII)
SERVICE_ACCESS_TEXT = "service access"
COMMON_LINUX_EXECUTABLE_DIRECTORIES = (Path("/snap/bin"),)
CI_ENVIRONMENT_KEYS = frozenset(
    (
        "CI",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "BUILDKITE",
        "TF_BUILD",
    )
)
CONTAINER_MARKER_FILES = (
    (".dockerenv",),
    ("run", ".containerenv"),
    ("var", "run", ".containerenv"),
)
CONTAINER_CGROUP_MARKERS = (
    "docker",
    "kubepods",
    "containerd",
    "libpod",
    "podman",
    "lxc",
)
WSL_MARKERS = ("microsoft", "wsl")
WSL_ENVIRONMENT_KEYS = ("WSL_DISTRO_NAME", "WSL_INTEROP")
WSL_INTEROP_MARKER_FILES = (("proc", "sys", "fs", "binfmt_misc", "WSLInterop"),)
API_STATUS_PATH = "/api/status"
WINDOWS_WSL_BRIDGE_STATE = Path("tools/windows/.tws-wsl-bridge.state.json")
DEFAULT_WINDOWS_WSL_BRIDGE_STATE_MAX_AGE_SECONDS = 7 * 24 * 60 * 60


class HostPreflightProbe(PortHostPreflightProbe):
    def __init__(
        self,
        root: Path | None = None,
        executable_fallback_directories: Sequence[Path] | None = None,
        *,
        os_root: Path | None = None,
        project_paths: ProjectPaths | None = None,
        windows_wsl_bridge_state_max_age_seconds: int = DEFAULT_WINDOWS_WSL_BRIDGE_STATE_MAX_AGE_SECONDS,
    ):
        self.root = root or (project_paths or default_project_paths()).repository_root
        self.os_root = os_root or Path("/")
        self.executable_fallback_directories = tuple(
            COMMON_LINUX_EXECUTABLE_DIRECTORIES
            if executable_fallback_directories is None
            else executable_fallback_directories
        )
        self.windows_wsl_bridge_state_max_age_seconds = windows_wsl_bridge_state_max_age_seconds

    def is_linux_or_wsl(self) -> bool:
        return platform.system().lower() == "linux"

    def host_environment_report(self) -> HostEnvironmentReport:
        platform_family = _safe_signal_token(platform.system())
        if platform_family != "linux":
            return HostEnvironmentReport(
                environment=HostEnvironmentKind.UNKNOWN_UNSUPPORTED,
                setup_path=SetupPath.UNSUPPORTED,
                remediation=("Run Tiny Swarm World from native Linux or WSL2.",),
                evidence={
                    "classification": "unknown_unsupported",
                    "kernel_family": platform_family,
                },
            )

        if self._has_container_marker():
            return self._sandbox_report("container_marker")

        if _has_ci_hint(os.environ):
            return self._sandbox_report("ci_marker")

        wsl_report = self._wsl_environment_report()
        if wsl_report is not None:
            return wsl_report

        if not self._has_kernel_signal():
            return self._sandbox_report("kernel_signal_missing")

        return HostEnvironmentReport(
            environment=HostEnvironmentKind.NATIVE_LINUX,
            setup_path=SetupPath.NATIVE_LINUX,
            remediation=("Verify Incus readiness before live setup.",),
            evidence={
                "classification": "native_linux",
                "kernel_family": "linux",
                "kernel_signal": "present",
                "sandbox_signal": "absent",
            },
        )

    def python_version(self) -> str:
        return ".".join(str(part) for part in sys.version_info[:3])

    def executable_available(self, name: str) -> bool:
        return shutil.which(
            name,
            path=_executable_search_path(self.executable_fallback_directories),
        ) is not None

    def cpu_count(self) -> int:
        return os.cpu_count() or 0

    def memory_bytes(self) -> int:
        meminfo = Path("/proc/meminfo")
        if not meminfo.exists():
            return 0
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                parts = line.split()
                if len(parts) >= 2:
                    return int(parts[1]) * 1024
        return 0

    def disk_free_bytes(self, path: str) -> int:
        target = self.root / path
        return shutil.disk_usage(target).free

    def port_available(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
            except PermissionError:
                return _privileged_port_without_listener(port)
            except OSError:
                return False
        return True

    def port_matches_expected_service(self, port: int, service: str) -> bool:
        service_name = service.casefold()
        if "portainer" in service_name:
            return _http_service_available(port, (API_STATUS_PATH, "/api/system/status"), ("version",))
        if "docker registry" in service_name:
            return _http_service_available(port, ("/v2/",), ())
        if "nexus" in service_name:
            return _http_service_available(
                port,
                ("/service/rest/v1/status", "/"),
                ("nexus", "status", "available"),
            )
        if "jenkins" in service_name:
            return _http_service_available(port, ("/login", "/"), ("jenkins",))
        if "pulsar admin" in service_name:
            return _http_service_available(port, ("/admin/v2/clusters",), ("standalone", "clusters"))
        if "pulsar manager" in service_name:
            return _http_service_available(port, ("/",), ("pulsar", "manager"))
        if "pulsar broker" in service_name:
            return _tcp_connects(port)
        if "sonarqube" in service_name:
            return _http_service_available(port, ("/api/system/status", "/"), ("sonar", "status"))
        if "swagger api" in service_name:
            return _http_service_available(port, ("/",), ("access-control-allow-origin: *",))
        if "swagger" in service_name:
            return _http_service_available(port, ("/",), ("swagger", "openapi"))
        if "traefik http ingress" in service_name:
            return _http_service_available(port, ("/",), ("traefik",))
        if "traefik https ingress" in service_name:
            return _http_service_available(
                port,
                ("/",),
                ("traefik",),
                scheme="https",
            )
        if SERVICE_ACCESS_TEXT in service_name:
            return _service_access_available(port)
        if "infisical https" in service_name:
            return _http_service_available(
                port,
                ("/", API_STATUS_PATH),
                ("infisical", "content-security-policy"),
                scheme="https",
            )
        if "infisical" in service_name:
            return _http_service_available(port, ("/", API_STATUS_PATH), ("infisical",))
        return False

    def secret_available(self, name: str) -> bool:
        return bool(os.environ.get(name))

    def path_ignored_by_git(self, path: str) -> bool:
        completed = subprocess.run(
            ["git", "check-ignore", "-q", "--", path],
            cwd=self.root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return completed.returncode == 0

    def forbidden_tracked_secret_fingerprints(
        self,
        fingerprints: Mapping[str, str],
    ) -> Sequence[str]:
        found: set[str] = set()
        for source_file in self._tracked_text_files():
            text = source_file.read_text(encoding="utf-8", errors="ignore")
            text_fingerprints = set(_token_fingerprints(text))
            for identifier, fingerprint in fingerprints.items():
                if fingerprint in text_fingerprints:
                    found.add(identifier)
        return tuple(sorted(found))

    def windows_wsl_bridge_status(
        self,
        expected_ports: Sequence[int],
    ) -> WindowsWslBridgeStatus:
        state_path = self.root / WINDOWS_WSL_BRIDGE_STATE
        relative_state_path = WINDOWS_WSL_BRIDGE_STATE.as_posix()
        expected = tuple(int(port) for port in expected_ports)
        if not state_path.exists():
            return WindowsWslBridgeStatus(
                prepared=False,
                reason="state_missing",
                state_path=relative_state_path,
                expected_ports=expected,
                missing_ports=expected,
            )

        try:
            raw_state = json.loads(state_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return WindowsWslBridgeStatus(
                prepared=False,
                reason="state_invalid",
                state_path=relative_state_path,
                expected_ports=expected,
                missing_ports=expected,
            )
        if not isinstance(raw_state, Mapping):
            return WindowsWslBridgeStatus(
                prepared=False,
                reason="state_invalid",
                state_path=relative_state_path,
                expected_ports=expected,
                missing_ports=expected,
            )

        mapped_ports = _mapped_ports_from_bridge_state(raw_state)
        missing_ports = tuple(sorted(set(expected) - set(mapped_ports)))
        generated_at = str(raw_state.get("generatedAt", ""))
        listen_address = str(raw_state.get("listenAddress", ""))
        state_wsl_ip = str(raw_state.get("wslIp", ""))
        current_wsl_ip = _current_wsl_ipv4()
        state_age_seconds = _state_age_seconds(generated_at)

        def bridge_status(prepared: bool, reason: str) -> WindowsWslBridgeStatus:
            return WindowsWslBridgeStatus(
                prepared=prepared,
                reason=reason,
                state_path=relative_state_path,
                current_wsl_ip=current_wsl_ip,
                state_wsl_ip=state_wsl_ip,
                generated_at=generated_at,
                listen_address=listen_address,
                expected_ports=expected,
                mapped_ports=mapped_ports,
                missing_ports=missing_ports,
                state_age_seconds=state_age_seconds,
            )

        if not generated_at:
            return bridge_status(False, "generated_at_missing")
        if state_age_seconds is None:
            return bridge_status(False, "generated_at_invalid")
        if state_age_seconds > self.windows_wsl_bridge_state_max_age_seconds:
            return bridge_status(False, "state_stale_by_age")
        if not current_wsl_ip:
            return bridge_status(False, "wsl_ip_unavailable")
        if state_wsl_ip != current_wsl_ip:
            return bridge_status(False, "wsl_ip_changed")
        if missing_ports:
            return bridge_status(False, "missing_ports")
        return bridge_status(True, "prepared")

    def _tracked_text_files(self) -> tuple[Path, ...]:
        suffixes = {".py", ".sh", ".yaml", ".yml", ".json", ".md", ".adoc"}
        completed = subprocess.run(
            ["git", "ls-files", "--", "src", "infra"],
            cwd=self.root,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        if completed.returncode == 0:
            return tuple(
                path
                for path in self._paths_from_git_output(completed.stdout)
                if path.suffix in suffixes
            )

        roots = (
            self.root / "src",
            self.root / "infra",
        )
        files: list[Path] = []
        for root in roots:
            if not root.exists():
                continue
            files.extend(
                path
                for path in root.rglob("*")
                if path.is_file() and path.suffix in suffixes
            )
        return tuple(files)

    def _paths_from_git_output(self, output: str) -> tuple[Path, ...]:
        root = self.root.resolve()
        paths: list[Path] = []
        for line in output.splitlines():
            candidate = (root / line).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                continue
            if candidate.is_file():
                paths.append(candidate)
        return tuple(paths)

    def _sandbox_report(self, signal: str) -> HostEnvironmentReport:
        return HostEnvironmentReport(
            environment=HostEnvironmentKind.SANDBOX_UNVERIFIED,
            setup_path=SetupPath.SANDBOX_UNVERIFIED,
            remediation=(
                "Use static validation only, or rerun from verified native Linux or WSL2.",
            ),
            evidence={
                "classification": "sandbox_unverified",
                "kernel_family": "linux",
                "sandbox_signal": signal,
            },
        )

    def _has_kernel_signal(self) -> bool:
        return bool(self._kernel_signal_text().strip())

    def _wsl_environment_report(self) -> HostEnvironmentReport | None:
        kernel_signal = self._kernel_signal_text()
        has_kernel_hint = _has_wsl_kernel_hint(kernel_signal)
        has_independent_signal = self._has_wsl_independent_signal()
        if not has_kernel_hint and not has_independent_signal:
            return None

        if _is_wsl2_kernel(kernel_signal) and has_independent_signal:
            return HostEnvironmentReport(
                environment=HostEnvironmentKind.WSL2,
                setup_path=SetupPath.WSL2,
                remediation=("Verify WSL2 Incus readiness before live setup.",),
                evidence={
                    "classification": "wsl2",
                    "kernel_family": "linux",
                    "sandbox_signal": "absent",
                    "wsl_generation": "2",
                    "wsl_kernel_signal": "present",
                    "wsl_independent_signal": "present",
                },
            )

        if _is_wsl1_kernel(kernel_signal) and has_independent_signal:
            return HostEnvironmentReport(
                environment=HostEnvironmentKind.WSL1_UNSUPPORTED,
                setup_path=SetupPath.UNSUPPORTED,
                remediation=("Upgrade the distribution to WSL2 or use native Linux.",),
                evidence={
                    "classification": "wsl1_unsupported",
                    "kernel_family": "linux",
                    "wsl_generation": "1",
                    "wsl_kernel_signal": "present",
                    "wsl_independent_signal": "present",
                },
            )

        return HostEnvironmentReport(
            environment=HostEnvironmentKind.UNKNOWN_UNSUPPORTED,
            setup_path=SetupPath.UNSUPPORTED,
            remediation=(
                "Verify the WSL generation from the same Linux shell before live setup.",
            ),
            evidence={
                "classification": "wsl_unknown",
                "kernel_family": "linux",
                "wsl_generation": "unknown",
                "wsl_kernel_signal": _presence_text(has_kernel_hint),
                "wsl_independent_signal": _presence_text(has_independent_signal),
            },
        )

    def _kernel_signal_text(self) -> str:
        return "\n".join(
            self._read_os_file(*parts).casefold()
            for parts in (
                ("proc", "version"),
                ("proc", "sys", "kernel", "osrelease"),
            )
        )

    def _has_wsl_independent_signal(self) -> bool:
        if any(os.environ.get(key) for key in WSL_ENVIRONMENT_KEYS):
            return True
        return any((self.os_root.joinpath(*parts)).exists() for parts in WSL_INTEROP_MARKER_FILES)

    def _has_container_marker(self) -> bool:
        if any((self.os_root.joinpath(*parts)).exists() for parts in CONTAINER_MARKER_FILES):
            return True
        text = "\n".join(
            self._read_os_file(*parts).casefold()
            for parts in (
                ("proc", "1", "cgroup"),
                ("proc", "self", "cgroup"),
            )
        )
        return any(marker in text for marker in CONTAINER_CGROUP_MARKERS)

    def _read_os_file(self, *parts: str) -> str:
        try:
            return self.os_root.joinpath(*parts).read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except OSError:
            return ""


def _mapped_ports_from_bridge_state(state: Mapping[object, object]) -> tuple[int, ...]:
    mappings = state.get("mappings", ())
    if not isinstance(mappings, Sequence) or isinstance(mappings, str):
        return ()
    ports: set[int] = set()
    for mapping in mappings:
        if not isinstance(mapping, Mapping):
            continue
        try:
            ports.add(int(mapping.get("listenPort", 0)))
        except (TypeError, ValueError):
            continue
    return tuple(sorted(port for port in ports if port > 0))


def _state_age_seconds(generated_at: str) -> int | None:
    generated = _parse_bridge_timestamp(generated_at)
    if generated is None:
        return None
    now = datetime.now(UTC)
    return max(0, int((now - generated).total_seconds()))


def _parse_bridge_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    normalized = re.sub(r"(\.\d{6})\d+([+-]\d{2}:\d{2})$", r"\1\2", normalized)
    normalized = re.sub(r"(\.\d{6})\d+$", r"\1", normalized)
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _current_wsl_ipv4() -> str:
    try:
        completed = subprocess.run(
            ["hostname", "-I"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if completed.returncode != 0:
        return ""
    for part in completed.stdout.split():
        if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", part):
            return part
    return ""


def _token_fingerprints(text: str) -> tuple[str, ...]:
    return tuple(
        hashlib.sha256(match.group(0).encode("utf-8")).hexdigest()
        for match in SECRET_TOKEN_PATTERN.finditer(text)
    )


def _has_ci_hint(environ: Mapping[str, str]) -> bool:
    return any(environ.get(key) for key in CI_ENVIRONMENT_KEYS)


def _safe_signal_token(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9_+-]", "_", value.casefold()).strip("_")
    return normalized[:40] or "unknown"


def _has_wsl_kernel_hint(kernel_signal: str) -> bool:
    return any(marker in kernel_signal for marker in WSL_MARKERS)


def _is_wsl2_kernel(kernel_signal: str) -> bool:
    return "microsoft" in kernel_signal and "wsl2" in kernel_signal


def _is_wsl1_kernel(kernel_signal: str) -> bool:
    return (
        "wsl2" not in kernel_signal
        and re.search(r"\b4\.4\.[^\n]*microsoft|microsoft[^\n]*\b4\.4\.", kernel_signal)
        is not None
    )


def _presence_text(value: bool) -> str:
    return "present" if value else "absent"


def _http_service_available(
    port: int,
    paths: Sequence[str],
    expected_markers: Sequence[str],
    *,
    scheme: str = "http",
) -> bool:
    for path in paths:
        try:
            status, text = _read_http_response(port, path, scheme=scheme)
        except OSError:
            continue
        if status >= 500:
            continue
        normalized_text = text.casefold()
        if not expected_markers or any(marker in normalized_text for marker in expected_markers):
            return True
    return False


def _service_access_available(port: int) -> bool:
    expected_markers = (SERVICE_ACCESS_TEXT, "infisical")
    return _http_service_available(
        port,
        ("/",),
        expected_markers,
    ) or _http_service_available(
        port,
        ("/",),
        expected_markers,
        scheme="https",
    )


def _privileged_port_without_listener(port: int) -> bool:
    if port >= 1024:
        return False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        try:
            return sock.connect_ex(("127.0.0.1", port)) != 0
        except OSError:
            return False


def _read_http_response(port: int, path: str, *, scheme: str = "http") -> tuple[int, str]:
    request = urllib.request.Request(
        f"{scheme}://127.0.0.1:{port}{path}",
        headers={"User-Agent": "tiny-swarm-world-preflight/1.0"},
    )
    try:
        context = _verified_tls_context() if scheme == "https" else None
        with urllib.request.urlopen(request, timeout=2.0, context=context) as response:
            return response.status, _response_text(response.read(4096), response.headers)
    except urllib.error.HTTPError as error:
        return error.code, _response_text(error.read(4096), error.headers)


def _verified_tls_context() -> ssl.SSLContext:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_default_certs()
    return context


def _response_text(body: bytes, headers: object) -> str:
    header_text = "\n".join(f"{key}: {value}" for key, value in getattr(headers, "items", lambda: ())())
    return f"{header_text}\n{body.decode('utf-8', errors='ignore')}"


def _tcp_connects(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2.0):
            return True
    except OSError:
        return False


def ensure_common_executable_paths(
    fallback_directories: Sequence[Path] = COMMON_LINUX_EXECUTABLE_DIRECTORIES,
) -> None:
    entries = _path_entries()
    present = set(entries)
    for directory in fallback_directories:
        directory_text = str(directory)
        if directory.is_dir() and directory_text not in present:
            entries.append(directory_text)
            present.add(directory_text)
    os.environ["PATH"] = os.pathsep.join(entries)


def _executable_search_path(fallback_directories: Sequence[Path]) -> str:
    entries = _path_entries()
    present = set(entries)
    for directory in fallback_directories:
        directory_text = str(directory)
        if directory.is_dir() and directory_text not in present:
            entries.append(directory_text)
            present.add(directory_text)
    return os.pathsep.join(entries)


def _path_entries() -> list[str]:
    return [entry for entry in os.environ.get("PATH", "").split(os.pathsep) if entry]
