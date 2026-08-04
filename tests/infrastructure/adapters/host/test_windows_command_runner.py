import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from tiny_swarm_world.infrastructure.adapters.host.windows_command_runner import (
    WindowsCommandRunner,
    _to_windows_path,
)


class _Process:
    def __init__(self, *, timeout: bool = False) -> None:
        self.timeout = timeout
        self.returncode = 0
        self.terminated = False
        self.killed = False
        self.commands: list[tuple[str, float | None]] = []

    def communicate(self, timeout=None):
        self.commands.append(("communicate", timeout))
        if self.timeout and not self.terminated and not self.killed:
            raise subprocess.TimeoutExpired("powershell.exe", timeout)
        return "out", "err"

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True


class _StuckProcess(_Process):
    def communicate(self, timeout=None):
        self.commands.append(("communicate", timeout))
        if not self.killed:
            raise subprocess.TimeoutExpired("powershell.exe", timeout)
        return "out", "err"


class _InterruptProcess(_Process):
    def communicate(self, timeout=None):
        if self.terminated:
            return "out", "err"
        raise KeyboardInterrupt


class TestWindowsCommandRunner(unittest.TestCase):
    def test_rejects_non_positive_timeout(self):
        runner = WindowsCommandRunner(popen=lambda command, **kwargs: _Process())

        with self.assertRaises(ValueError):
            runner.run(
                "verify",
                script_path=Path("bridge.ps1"),
                config_path=Path("bridge.json"),
                port_registry_path=Path("ports.yaml"),
                timeout_seconds=0,
            )

    def test_uses_dedicated_powershell_boundary_and_converts_paths(self):
        process = _Process()
        calls: list[list[str]] = []

        def popen(command, **kwargs):
            calls.append(command)
            self.assertFalse(kwargs["shell"])
            return process

        runner = WindowsCommandRunner(
            path_converter=lambda path: f"WIN:{path.as_posix()}",
            popen=popen,
        )

        result = runner.run(
            "refresh",
            script_path=Path("bridge.ps1"),
            config_path=Path("bridge.json"),
            port_registry_path=Path("ports.yaml"),
            timeout_seconds=7,
        )

        self.assertEqual(0, result.return_code)
        self.assertEqual("powershell.exe", calls[0][0])
        self.assertIn("-Action", calls[0])
        self.assertIn("refresh", calls[0])
        self.assertIn("WIN:bridge.ps1", calls[0])

    def test_timeout_terminates_then_kills_child_and_returns_typed_status(self):
        process = _Process(timeout=True)
        runner = WindowsCommandRunner(
            path_converter=lambda path: path.as_posix(),
            popen=lambda command, **kwargs: process,
            termination_grace_seconds=0.01,
        )

        result = runner.run(
            "verify",
            script_path=Path("bridge.ps1"),
            config_path=Path("bridge.json"),
            port_registry_path=Path("ports.yaml"),
            timeout_seconds=0.01,
        )

        self.assertTrue(result.timed_out)
        self.assertTrue(process.terminated)
        self.assertFalse(process.killed)

    def test_timeout_kills_child_after_grace_period(self):
        process = _StuckProcess()
        runner = WindowsCommandRunner(
            path_converter=lambda path: path.as_posix(),
            popen=lambda command, **kwargs: process,
            termination_grace_seconds=0.01,
        )

        result = runner.run(
            "verify",
            script_path=Path("bridge.ps1"),
            config_path=Path("bridge.json"),
            port_registry_path=Path("ports.yaml"),
            timeout_seconds=0.01,
        )

        self.assertTrue(result.timed_out)
        self.assertTrue(process.terminated)
        self.assertTrue(process.killed)

    def test_interrupt_and_os_error_are_typed(self):
        interrupted = _InterruptProcess()
        result = WindowsCommandRunner(
            path_converter=lambda path: path.as_posix(),
            popen=lambda command, **kwargs: interrupted,
        ).run(
            "verify",
            script_path=Path("bridge.ps1"),
            config_path=Path("bridge.json"),
            port_registry_path=Path("ports.yaml"),
            timeout_seconds=1,
        )
        self.assertTrue(result.interrupted)

        def fail_popen(command, **kwargs):
            raise OSError("powershell unavailable")

        result = WindowsCommandRunner(popen=fail_popen).run(
            "verify",
            script_path=Path("bridge.ps1"),
            config_path=Path("bridge.json"),
            port_registry_path=Path("ports.yaml"),
            timeout_seconds=1,
        )
        self.assertEqual("OSError", result.stderr)

    @patch("tiny_swarm_world.infrastructure.adapters.host.windows_command_runner.subprocess.run")
    def test_path_conversion_rejects_failed_wslpath(self, run):
        run.return_value = subprocess.CompletedProcess(("wslpath",), 1, "", "")

        with self.assertRaisesRegex(OSError, "wslpath"):
            _to_windows_path(Path("/mnt/d/project"))
