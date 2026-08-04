from __future__ import annotations

import subprocess
from collections.abc import Callable

from tiny_swarm_world.domain.preflight.hang_diagnostics import (
    HangDiagnosticCommand,
    HangDiagnosticReport,
)


CommandRunner = Callable[[str, tuple[str, ...], float], HangDiagnosticCommand]


class ReadOnlyHangDiagnostics:
    def __init__(self, runner: CommandRunner | None = None, timeout_seconds: float = 10.0) -> None:
        if timeout_seconds <= 0:
            raise ValueError("Hang diagnostics timeout must be positive.")
        self.runner = runner or _run_command
        self.timeout_seconds = timeout_seconds

    def collect(self) -> HangDiagnosticReport:
        commands = (
            ("processes", ("ps", "-eo", "pid,ppid,stat,etime,%cpu,%mem,wchan:30,cmd")),
            ("tiny_swarm_world", ("pgrep", "-af", "tiny_swarm_world")),
            ("docker_services", ("docker", "service", "ls")),
            ("docker_tasks", ("docker", "service", "ps", "--all")),
            ("docker_stacks", ("docker", "stack", "ls")),
            (
                "docker_logs",
                (
                    "sh",
                    "-lc",
                    "docker ps -q | xargs -r -n1 docker logs --tail 100 --timestamps",
                ),
            ),
            ("incus_containers", ("incus", "list")),
            (
                "cgroup_memory",
                (
                    "sh",
                    "-lc",
                    "for name in memory.current memory.max memory.high memory.events memory.stat; do "
                    "printf '%s\\n' \"---$name\"; "
                    "if [ -r /sys/fs/cgroup/$name ]; then cat /sys/fs/cgroup/$name; else printf '%s\\n' unavailable; fi; "
                    "done",
                ),
            ),
            (
                "network_state",
                ("sh", "-lc", "ip -brief address; ip route; ss -lntup"),
            ),
        )
        return HangDiagnosticReport(
            tuple(self.runner(name, args, self.timeout_seconds) for name, args in commands)
        )


def _run_command(name: str, args: tuple[str, ...], timeout: float) -> HangDiagnosticCommand:
    try:
        completed = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return HangDiagnosticCommand(name, "TIMED_OUT", "", True, "unknown")
    except OSError as exc:
        return HangDiagnosticCommand(name, "UNAVAILABLE", str(exc), classification="unknown")
    output = completed.stdout[-8192:]
    status = "OK" if completed.returncode == 0 else "FAILED"
    return HangDiagnosticCommand(name, status, output, classification=_classify(name, output))


def _classify(name: str, output: str) -> str:
    """Classify observed state without changing any process or runtime state."""
    lowered = output.lower()
    if name == "processes":
        if "<defunct>" in lowered or "z    " in lowered:
            return "exited_uncollected"
        if any(marker in lowered for marker in ("io_schedule", "wait_on_page", "blk_", "jbd2")):
            return "io_wait"
        if any(marker in lowered for marker in ("sock_", "tcp_", "dns", "poll_schedule_timeout")):
            return "network_wait"
        if any(marker in lowered for marker in (" d ", "pipe_read", "futex")):
            return "blocked_child"
        if _contains_high_cpu_process(output):
            return "cpu_bound"
        return "active" if output.strip() else "unknown"
    if name in {"docker_services", "docker_tasks", "docker_stacks", "docker_logs", "incus_containers"}:
        return "active" if output.strip() else "unknown"
    return "active" if output.strip() else "unknown"


def _contains_high_cpu_process(output: str) -> bool:
    for line in output.splitlines()[1:]:
        fields = line.split(None, 7)
        if len(fields) < 6:
            continue
        try:
            if float(fields[4]) >= 80.0:
                return True
        except ValueError:
            continue
    return False
