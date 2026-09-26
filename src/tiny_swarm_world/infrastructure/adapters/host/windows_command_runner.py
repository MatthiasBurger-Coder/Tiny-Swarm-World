from __future__ import annotations

from tiny_swarm_world.infrastructure.process.runner import run_process
from tiny_swarm_world.infrastructure.process.streaming import ProcessFactory, run_captured_process

import os
from collections.abc import Callable
from pathlib import Path

from tiny_swarm_world.application.ports.host import (
    PortWindowsCommandRunner,
    WindowsCommandResult,
)


PathConverter = Callable[[Path], str]


class WindowsCommandRunner(PortWindowsCommandRunner):
    """Bounded PowerShell runner; Windows commands remain inside infrastructure."""

    def __init__(
        self,
        *,
        executable: str = "powershell.exe",
        path_converter: PathConverter | None = None,
        popen: ProcessFactory | None = None,
        termination_grace_seconds: float = 3.0,
    ) -> None:
        self.executable = executable
        self.path_converter = path_converter or _to_windows_path
        self.popen = popen
        self.termination_grace_seconds = termination_grace_seconds

    def run(
        self,
        action: str,
        *,
        script_path: Path,
        config_path: Path,
        port_registry_path: Path,
        timeout_seconds: float,
    ) -> WindowsCommandResult:
        if timeout_seconds <= 0:
            raise ValueError("Windows command timeout must be positive.")
        command = [
            self.executable,
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            self.path_converter(script_path),
            "-Action",
            action,
            "-ConfigPath",
            self.path_converter(config_path),
            "-PortRegistryPath",
            self.path_converter(port_registry_path),
        ]
        result = run_captured_process(
            command, timeout=timeout_seconds, popen=self.popen,
            termination_grace_seconds=self.termination_grace_seconds,
        )
        return WindowsCommandResult(
            result.returncode, stdout=result.stdout, stderr=result.stderr,
            timed_out=result.timed_out, interrupted=result.interrupted,
        )


def _to_windows_path(path: Path) -> str:
    value = path.as_posix()
    if os.name == "nt" and not value.startswith("/"):
        return value
    result = run_process(
        ["wslpath", "-w", value],
        capture_output=True,
        text=True,
        check=False,
        timeout=5.0,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise OSError("wslpath could not convert the Windows bridge path")
    return result.stdout.strip()
