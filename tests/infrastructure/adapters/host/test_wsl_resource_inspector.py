import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tiny_swarm_world.infrastructure.adapters.host.wsl_resource_inspector import (
    WslResourceInspector,
    _current_cgroup_root,
    _parse_psi_avg10,
    _run_free_bytes,
    _run_nproc,
)


class TestWslResourceInspector(unittest.TestCase):
    def test_inspect_uses_nproc_and_free_b_signals(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(root / "proc/meminfo", "MemTotal:       17179869184 kB\n")
            _write(root / "sys/fs/cgroup/memory.max", "max\n")
            _write(root / "sys/fs/cgroup/memory.current", "1024\n")

            def run(command, **kwargs):
                self.assertEqual(5.0, kwargs["timeout"])
                if command == ["nproc"]:
                    return subprocess.CompletedProcess(command, 0, "12\n", "")
                if command == ["free", "-b"]:
                    return subprocess.CompletedProcess(
                        command,
                        0,
                        "              total        used        free\n"
                        "Mem:   17179869184 1000 17179868184\n",
                        "",
                    )
                raise AssertionError(command)

            with patch(
                "tiny_swarm_world.infrastructure.adapters.host.wsl_resource_inspector.subprocess.run",
                side_effect=run,
            ):
                resources = WslResourceInspector(root, run_system_commands=True).inspect(root)

        self.assertEqual(12, resources.cpu_threads)
        self.assertEqual(17179869184, resources.memory_bytes)
        self.assertEqual("nproc", resources.cpu_signal)
        self.assertEqual("free -b", resources.memory_signal)

    def test_inspect_reads_nested_current_process_cgroup_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(root / "proc/meminfo", "MemTotal:       17179869184 kB\n")
            _write(root / "proc/self/cgroup", "0::/user.slice/test.scope\n")
            _write(root / "sys/fs/cgroup/memory.max", "max\n")
            _write(root / "sys/fs/cgroup/user.slice/test.scope/memory.max", "8589934592\n")
            _write(root / "sys/fs/cgroup/user.slice/test.scope/memory.current", "1024\n")

            resources = WslResourceInspector(root).inspect(root)

        self.assertEqual(8589934592, resources.cgroup_memory_limit_bytes)
        self.assertEqual(8589934592, resources.effective_memory_bytes)

    def test_memory_pressure_reports_psi_and_oom_kill(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(root / "sys/fs/cgroup/memory.max", "100\n")
            _write(root / "sys/fs/cgroup/memory.current", "99\n")
            _write(root / "sys/fs/cgroup/memory.high", "80\n")
            _write(root / "sys/fs/cgroup/memory.events", "oom 2\noom_kill 1\npgscan 7\n")
            _write(root / "sys/fs/cgroup/memory.stat", "anon 42\n")
            _write(root / "sys/fs/cgroup/memory.pressure", "some avg10=2.50 avg60=1.0\n")

            pressure = WslResourceInspector(root).memory_pressure()

        self.assertEqual("oom_kill_detected", pressure.assessment)
        self.assertEqual(1, pressure.oom_kill_events)
        self.assertEqual(2.5, pressure.psi_some_avg10)
        self.assertEqual(7, pressure.reclaim_events)

    def test_nested_cgroup_resolution_fails_closed_for_invalid_membership(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write(root / "proc/self/cgroup", "0::../escape\n1:name=/legacy\n")

            self.assertEqual(root / "sys/fs/cgroup", _current_cgroup_root(root))

    @patch("tiny_swarm_world.infrastructure.adapters.host.wsl_resource_inspector.subprocess.run")
    def test_system_resource_probes_return_none_on_failures(self, run):
        run.side_effect = OSError("missing")
        self.assertIsNone(_run_nproc())
        self.assertIsNone(_run_free_bytes())

    def test_psi_parser_ignores_malformed_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.pressure"
            _write(path, "full avg10=1.0\nsome avg10=invalid\n")
            self.assertIsNone(_parse_psi_avg10(path))


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
