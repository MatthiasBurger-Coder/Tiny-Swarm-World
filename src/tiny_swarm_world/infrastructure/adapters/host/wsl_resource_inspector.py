from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from tiny_swarm_world.domain.preflight.resources import HostResources, MemoryPressureReport


class WslResourceInspector:
    def __init__(self, root: Path = Path("/"), *, run_system_commands: bool | None = None) -> None:
        self.root = root
        self.run_system_commands = root == Path("/") if run_system_commands is None else run_system_commands

    def inspect(self, disk_path: Path | None = None) -> HostResources:
        proc = self.root / "proc"
        meminfo = _parse_key_values(proc / "meminfo")
        nproc_threads = _run_nproc() if self.run_system_commands else None
        free_memory = _run_free_bytes() if self.run_system_commands else None
        cgroup = _current_cgroup_root(self.root)
        limit = _parse_cgroup_value(cgroup / "memory.max")
        current = _parse_cgroup_value(cgroup / "memory.current") or 0
        disk = shutil.disk_usage(disk_path or self.root).free
        return HostResources(
            cpu_threads=nproc_threads or os.cpu_count() or 0,
            memory_bytes=free_memory or meminfo.get("MemTotal", 0) * 1024,
            cgroup_memory_limit_bytes=limit,
            current_memory_usage_bytes=current,
            free_disk_bytes=disk,
            cpu_signal="nproc" if nproc_threads is not None else "os.cpu_count",
            memory_signal="free -b" if free_memory is not None else "/proc/meminfo",
        )

    def memory_pressure(self) -> MemoryPressureReport:
        cgroup = _current_cgroup_root(self.root)
        current = _parse_cgroup_value(cgroup / "memory.current") or 0
        maximum = _parse_cgroup_value(cgroup / "memory.max")
        high = _parse_cgroup_value(cgroup / "memory.high")
        events = _parse_key_values(cgroup / "memory.events")
        memory_stat = _parse_key_values(cgroup / "memory.stat")
        psi_some_avg10 = _parse_psi_avg10(cgroup / "memory.pressure")
        near_max = maximum is not None and current >= maximum * 0.95
        oom_kill = events.get("oom_kill", 0)
        oom = events.get("oom", 0)
        high_pressure = high is not None and current >= high
        if oom_kill:
            assessment, confidence = "oom_kill_detected", "high"
        elif oom:
            assessment, confidence = "oom_event_detected", "high"
        elif high_pressure:
            assessment, confidence = "memory_high_pressure", "high"
        elif near_max:
            assessment, confidence = "critical_memory_pressure", "medium"
        else:
            assessment, confidence = "no_confirmed_memory_pressure", "high"
        return MemoryPressureReport(
            memory_current=current,
            memory_max=maximum,
            memory_high=high,
            oom_events=oom,
            oom_kill_events=oom_kill,
            reclaim_events=events.get("pgscan", 0),
            assessment=assessment,
            confidence=confidence,
            memory_stat=memory_stat,
            psi_some_avg10=psi_some_avg10,
        )


def _current_cgroup_root(root: Path) -> Path:
    """Resolve the cgroup-v2 directory governing the current process.

    WSL and systemd commonly place a command in a nested scope with a tighter
    memory limit than the cgroup filesystem root. Reading only the root
    ``memory.max`` would therefore report ``unlimited`` and bypass the
    resource gate. Fixture roots without ``/proc/self/cgroup`` retain the
    historical root-level behavior.
    """

    cgroup_root = root / "sys/fs/cgroup"
    cgroup_membership = root / "proc/self/cgroup"
    if not cgroup_membership.exists():
        return cgroup_root
    try:
        lines = cgroup_membership.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return cgroup_root
    for line in lines:
        hierarchy, _controllers, relative_path = _split_cgroup_membership(line)
        if hierarchy != "0":
            continue
        relative = Path(relative_path.lstrip("/"))
        if any(part == ".." for part in relative.parts):
            return cgroup_root
        candidate = cgroup_root / relative
        if candidate.is_dir():
            return candidate
    return cgroup_root


def _split_cgroup_membership(line: str) -> tuple[str, str, str]:
    parts = line.split(":", 2)
    if len(parts) != 3:
        return "", "", ""
    return parts[0], parts[1], parts[2].strip()


def _parse_key_values(path: Path) -> dict[str, int]:
    if not path.exists():
        return {}
    result: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.split()
        if len(parts) >= 2:
            try:
                result[parts[0].rstrip(":")] = int(parts[1])
            except ValueError:
                continue
    return result


def _parse_cgroup_value(path: Path) -> int | None:
    if not path.exists():
        return None
    value = path.read_text(encoding="utf-8", errors="ignore").strip()
    if value == "max" or not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_psi_avg10(path: Path) -> float | None:
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.startswith("some "):
            continue
        for item in line.split()[1:]:
            key, separator, value = item.partition("=")
            if key == "avg10" and separator:
                try:
                    return float(value)
                except ValueError:
                    return None
    return None


def _run_nproc() -> int | None:
    try:
        result = subprocess.run(
            ["nproc"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        value = int(result.stdout.strip())
    except ValueError:
        return None
    return value if value > 0 else None


def _run_free_bytes() -> int | None:
    try:
        result = subprocess.run(
            ["free", "-b"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        fields = line.split()
        if fields and fields[0].rstrip(":").casefold() == "mem" and len(fields) >= 2:
            try:
                value = int(fields[1])
            except ValueError:
                return None
            return value if value > 0 else None
    return None
