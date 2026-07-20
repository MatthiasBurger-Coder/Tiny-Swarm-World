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
        )
        return HangDiagnosticReport(
            tuple(self.runner(name, args, self.timeout_seconds) for name, args in commands)
        )


def _run_command(name: str, args: tuple[str, ...], timeout: float) -> HangDiagnosticCommand:
    try:
        completed = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return HangDiagnosticCommand(name, "TIMED_OUT", "", True)
    except OSError as exc:
        return HangDiagnosticCommand(name, "UNAVAILABLE", str(exc))
    return HangDiagnosticCommand(name, "OK" if completed.returncode == 0 else "FAILED", completed.stdout[-8192:])
