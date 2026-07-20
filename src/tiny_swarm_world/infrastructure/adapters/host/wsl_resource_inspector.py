from __future__ import annotations

import os
import shutil
from pathlib import Path

from tiny_swarm_world.domain.preflight.resources import HostResources, MemoryPressureReport


class WslResourceInspector:
    def __init__(self, root: Path = Path("/")) -> None:
        self.root = root

    def inspect(self, disk_path: Path | None = None) -> HostResources:
        proc = self.root / "proc"
        meminfo = _parse_key_values(proc / "meminfo")
        limit = _parse_cgroup_value(self.root / "sys/fs/cgroup/memory.max")
        current = _parse_cgroup_value(self.root / "sys/fs/cgroup/memory.current") or 0
        disk = shutil.disk_usage(disk_path or self.root).free
        return HostResources(
            cpu_threads=os.cpu_count() or 0,
            memory_bytes=meminfo.get("MemTotal", 0) * 1024,
            cgroup_memory_limit_bytes=limit,
            current_memory_usage_bytes=current,
            free_disk_bytes=disk,
        )

    def memory_pressure(self) -> MemoryPressureReport:
        cgroup = self.root / "sys/fs/cgroup"
        current = _parse_cgroup_value(cgroup / "memory.current") or 0
        maximum = _parse_cgroup_value(cgroup / "memory.max")
        high = _parse_cgroup_value(cgroup / "memory.high")
        events = _parse_key_values(cgroup / "memory.events")
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
            current, maximum, high, oom, oom_kill, events.get("pgscan", 0), assessment, confidence
        )


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
