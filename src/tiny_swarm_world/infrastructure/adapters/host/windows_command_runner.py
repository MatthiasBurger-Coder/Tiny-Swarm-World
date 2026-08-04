from __future__ import annotations

import os
import subprocess
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
        popen: Callable[..., subprocess.Popen[str]] | None = None,
        termination_grace_seconds: float = 3.0,
    ) -> None:
        self.executable = executable
        self.path_converter = path_converter or _to_windows_path
        self.popen = popen or subprocess.Popen
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
        try:
            process = self.popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
                start_new_session=True,
            )
            stdout, stderr = process.communicate(timeout=timeout_seconds)
            return WindowsCommandResult(process.returncode, stdout=stdout, stderr=stderr)
        except subprocess.TimeoutExpired as exc:
            stdout, stderr = self._terminate(process)
            return WindowsCommandResult(
                process.returncode,
                timed_out=True,
                stdout=_coalesce_output(stdout, exc.stdout),
                stderr=_coalesce_output(stderr, exc.stderr),
            )
        except KeyboardInterrupt:
            stdout, stderr = self._terminate(process)
            return WindowsCommandResult(
                process.returncode,
                interrupted=True,
                stdout=stdout,
                stderr=stderr,
            )
        except OSError as exc:
            return WindowsCommandResult(None, stderr=type(exc).__name__)

    def _terminate(self, process: subprocess.Popen[str]) -> tuple[str, str]:
        try:
            process.terminate()
            stdout, stderr = process.communicate(timeout=self.termination_grace_seconds)
            return stdout, stderr
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            return stdout, stderr


def _to_windows_path(path: Path) -> str:
    value = path.as_posix()
    if os.name == "nt" and not value.startswith("/"):
        return value
    result = subprocess.run(
        ["wslpath", "-w", value],
        capture_output=True,
        text=True,
        check=False,
        timeout=5.0,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise OSError("wslpath could not convert the Windows bridge path")
    return result.stdout.strip()


def _coalesce_output(primary: str | bytes | None, secondary: str | bytes | None) -> str:
    value = primary if primary is not None else secondary
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value or ""
