from __future__ import annotations

import hashlib
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
from pathlib import Path

from tiny_swarm_world.application.ports.host import PortHostEnvironmentDetector
from tiny_swarm_world.application.ports.preflight import PortHostPreflightProbe
from tiny_swarm_world.domain.preflight import HostEnvironmentReport, WindowsWslBridgeStatus
from tiny_swarm_world.infrastructure.adapters.host import HostEnvironmentDetector
from tiny_swarm_world.infrastructure.adapters.preflight.windows_wsl_bridge_state import (
    DEFAULT_WINDOWS_WSL_BRIDGE_STATE_MAX_AGE_SECONDS,
    WINDOWS_WSL_BRIDGE_STATE,
    current_wsl_ipv4,
    windows_wsl_bridge_status,
)
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths, default_project_paths


SECRET_TOKEN_PATTERN = re.compile(r"\w[\w-]{2,}", re.ASCII)
SERVICE_ACCESS_TEXT = "service access"
COMMON_LINUX_EXECUTABLE_DIRECTORIES = (Path("/snap/bin"),)
API_STATUS_PATH = "/api/status"


class HostPreflightProbe(PortHostPreflightProbe):
    def __init__(
        self,
        root: Path | None = None,
        executable_fallback_directories: Sequence[Path] | None = None,
        *,
        os_root: Path | None = None,
        project_paths: ProjectPaths | None = None,
        host_environment_detector: PortHostEnvironmentDetector | None = None,
        windows_wsl_bridge_state_max_age_seconds: int = DEFAULT_WINDOWS_WSL_BRIDGE_STATE_MAX_AGE_SECONDS,
        windows_wsl_bridge_state_path: Path = WINDOWS_WSL_BRIDGE_STATE,
    ):
        self.root = root or (project_paths or default_project_paths()).repository_root
        self.os_root = os_root or Path("/")
        self.host_environment_detector = (
            host_environment_detector
            or HostEnvironmentDetector(
                os_root=self.os_root,
                platform_system=lambda: platform.system(),
            )
        )
        self.executable_fallback_directories = tuple(
            COMMON_LINUX_EXECUTABLE_DIRECTORIES
            if executable_fallback_directories is None
            else executable_fallback_directories
        )
        self.windows_wsl_bridge_state_max_age_seconds = windows_wsl_bridge_state_max_age_seconds
        self.windows_wsl_bridge_state_path = windows_wsl_bridge_state_path

    def is_linux_or_wsl(self) -> bool:
        return self.host_environment_report().platform_family == "linux"

    def host_environment_report(self) -> HostEnvironmentReport:
        return self.host_environment_detector.detect()

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
        return windows_wsl_bridge_status(
            self.root,
            expected_ports,
            state_path=self.windows_wsl_bridge_state_path,
            max_age_seconds=self.windows_wsl_bridge_state_max_age_seconds,
            current_wsl_ipv4=current_wsl_ipv4,
        )

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

def _token_fingerprints(text: str) -> tuple[str, ...]:
    return tuple(
        hashlib.sha256(match.group(0).encode("utf-8")).hexdigest()
        for match in SECRET_TOKEN_PATTERN.finditer(text)
    )


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
