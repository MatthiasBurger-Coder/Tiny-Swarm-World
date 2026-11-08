"""Read-only native host facts for the Ubuntu preparation boundary."""

from __future__ import annotations

import os
from dataclasses import replace
import platform
import shutil
import socket
from pathlib import Path

from tiny_swarm_world.domain.native_preparation import HOST_PORTS_BY_PROFILE, NativeHostFacts
from tiny_swarm_world.infrastructure.process import ProcessLaunchError, ProcessTimeoutError, SubprocessProcessRunner


class NativePreparationInspector:
    def __init__(self, repository_root: Path, *, service_profile: str = "service-access") -> None:
        self.repository_root = repository_root
        self.service_profile = service_profile

    def inspect(self) -> NativeHostFacts:
        release = _os_release()
        kernel = _read(Path("/proc/sys/kernel/osrelease")).casefold()
        version = _read(Path("/proc/version")).casefold()
        return NativeHostFacts(
            platform=platform.system(),
            is_wsl="microsoft" in kernel or "wsl" in kernel or "microsoft" in version,
            distribution_id=release.get("ID", ""),
            version_id=release.get("VERSION_ID", ""),
            architecture=platform.machine(),
            cpu_count=os.cpu_count() or 0,
            memory_bytes=_memory_bytes(),
            free_disk_bytes=shutil.disk_usage(self.repository_root).free,
            can_install_packages=_can_install_packages(),
            repository_writable=os.access(self.repository_root, os.W_OK),
            kernel_ready=_kernel_ready(),
            ports_ready=all(
                _port_available(port) for port in HOST_PORTS_BY_PROFILE[self.service_profile]
            ),
            conflicting_runtime=_conflicting_runtime(),
            network_ready=_network_ready(),
        )


def _os_release() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in _read(Path("/etc/os-release")).splitlines():
        key, separator, value = line.partition("=")
        if separator and key in {"ID", "VERSION_ID"}:
            values[key] = value.strip().strip('"').strip("'")
    return values


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _memory_bytes() -> int:
    for line in _read(Path("/proc/meminfo")).splitlines():
        if line.startswith("MemTotal:"):
            fields = line.split()
            if len(fields) >= 2 and fields[1].isdigit():
                return int(fields[1]) * 1024
    return 0


def _can_install_packages() -> bool:
    if os.geteuid() == 0:
        return True
    if shutil.which("sudo") is None:
        return False
    try:
        result = SubprocessProcessRunner().run_text(
            ("sudo", "-n", "-l", "/usr/bin/apt-get"),
            capture_output=True,
            timeout=5.0,
        )
    except (ProcessLaunchError, ProcessTimeoutError):
        return False
    return result.returncode == 0


def _port_available(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("0.0.0.0", port))
        return True
    except PermissionError:
        # Unprivileged bind restrictions alone do not mean a listener exists.
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return False
        except OSError:
            return True
    except OSError:
        return False


def _conflicting_runtime() -> bool:
    if shutil.which("lxd") is None:
        return False
    if shutil.which("systemctl") is None:
        return True
    runner = SubprocessProcessRunner()
    for unit in ("lxd.service", "snap.lxd.daemon.service", "snap.lxd.daemon.unix.socket"):
        try:
            result = runner.run_text(
                ("systemctl", "is-active", "--quiet", unit),
                capture_output=True,
                timeout=5.0,
            )
        except (ProcessLaunchError, ProcessTimeoutError):
            return True
        if result.returncode == 0:
            return True
    return False


def _kernel_ready() -> bool:
    return all(
        _read(Path("/proc/sys") / relative).strip() == "1"
        for relative in (
            "net/bridge/bridge-nf-call-iptables",
            "net/bridge/bridge-nf-call-ip6tables",
            "net/ipv4/ip_forward",
        )
    )


def _network_ready() -> bool:
    for port in (443, 80):
        try:
            with socket.create_connection(("archive.ubuntu.com", port), timeout=3.0):
                return True
        except OSError:
            continue
    return False


class WslUbuntuPreparationInspector(NativePreparationInspector):
    """Linux-only WSL facts; no Windows configuration or bridge ownership."""

    def inspect(self) -> NativeHostFacts:
        facts = super().inspect()
        kernel = _read(Path("/proc/sys/kernel/osrelease")).casefold()
        return replace(facts, wsl2="microsoft-standard" in kernel,
                       systemd_ready=Path("/run/systemd/system").is_dir())
