from __future__ import annotations

import subprocess
import unittest
from unittest.mock import Mock, patch

from tiny_swarm_world.infrastructure.adapters.native_package_manager import (
    AptHostPackageManager,
)


class AptHostPackageManagerTests(unittest.TestCase):
    def test_inventory_and_install_only_missing_packages(self) -> None:
        runner = Mock()
        runner.run_text.side_effect = (
            subprocess.CompletedProcess((), 0, "install ok installed", ""),
            subprocess.CompletedProcess((), 1, "", ""),
            subprocess.CompletedProcess((), 0, "", ""),
            subprocess.CompletedProcess((), 0, "", ""),
        )
        manager = AptHostPackageManager(runner)
        missing = manager.missing(("curl", "incus"))
        self.assertEqual(missing, ("incus",))
        with patch("os.geteuid", return_value=1000):
            manager.install(missing)
        commands = [call.args[0] for call in runner.run_text.call_args_list]
        self.assertEqual(commands[2][:3], ("sudo", "apt-get", "update"))
        self.assertEqual(commands[3][-1], "incus")
        self.assertNotIn("curl", commands[3])
        self.assertTrue(runner.run_text.call_args_list[2].kwargs["capture_output"])
        self.assertTrue(runner.run_text.call_args_list[3].kwargs["capture_output"])

    def test_apt_failure_does_not_run_install_after_failed_update(self) -> None:
        runner = Mock()
        runner.run_text.return_value = subprocess.CompletedProcess((), 1, "", "")
        with self.assertRaisesRegex(RuntimeError, "index update failed"):
            AptHostPackageManager(runner).install(("incus",))
        self.assertEqual(runner.run_text.call_count, 1)


if __name__ == "__main__":
    unittest.main()
