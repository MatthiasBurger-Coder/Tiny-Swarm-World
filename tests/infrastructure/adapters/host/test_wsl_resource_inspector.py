import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tiny_swarm_world.infrastructure.adapters.host.wsl_resource_inspector import (
    WslResourceInspector,
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


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
