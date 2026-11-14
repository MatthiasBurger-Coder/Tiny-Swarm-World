"""Dependent-stage execution in disposable Linux fixtures."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class TestInstallHandoff(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="tsw-handoff-", dir=Path.home())
        self.addCleanup(self.temporary.cleanup)
        self.checkout = Path(self.temporary.name) / "checkout with spaces"
        self.checkout.mkdir()
        bootstrap = self.checkout / "modules/tsw_native_linux/boostrap"
        bootstrap.mkdir(parents=True)
        for name in ("install.sh", "prepare_linux.sh"):
            path = bootstrap / name
            path.write_text("#!/bin/sh\n")
            path.chmod(0o755)

    def test_preparation_failure_stops_install_and_shell_keeps_stdin_and_exit(self):
        for prepare_exit, install_exit in ((2, 0), (3, 0), (4, 0), (124, 0), (130, 0), (0, 17), (0, 0)):
            with self.subTest(prepare_exit=prepare_exit, install_exit=install_exit):
                marker = self.checkout / "called"
                marker.unlink(missing_ok=True)
                (self.checkout / "modules/tsw_native_linux/boostrap/prepare_linux.sh").write_text(f"#!/bin/sh\nread answer\n[ \"$answer\" = yes ] || exit 2\nexit {prepare_exit}\n")
                (self.checkout / "modules/tsw_native_linux/boostrap/install.sh").write_text(f"#!/bin/sh\ntouch called\nexit {install_exit}\n")
                chain = f"cd -- '{self.checkout}' && ./modules/tsw_native_linux/boostrap/prepare_linux.sh --service-profile default && exec ./modules/tsw_native_linux/boostrap/install.sh --service-profile default"
                result = subprocess.run(["bash", "-lc", chain], input="yes\n", text=True, capture_output=True,
                                        env={**os.environ}, check=False, timeout=10)
                self.assertEqual(result.returncode, prepare_exit or install_exit)
                self.assertEqual(marker.exists(), prepare_exit == 0)
