import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import security_gate


class TestSecurityGate(unittest.TestCase):
    def test_dependency_audit_uses_hashed_runtime_lock_without_resolution(self):
        command = security_gate._dependency_audit_command()

        self.assertIn("--disable-pip", command)
        self.assertIn("--strict", command)
        self.assertEqual(str(security_gate.RUNTIME_LOCK), command[-1])

    def test_sbom_output_is_restricted_to_ignored_local_state(self):
        with tempfile.TemporaryDirectory() as directory:
            outside = Path(directory) / "sbom.json"

            with self.assertRaises(SystemExit):
                security_gate._require_ignored_local_output(outside)

    def test_container_config_check_requires_explicit_trivy_installation(self):
        with patch("sys.argv", ["security_gate.py", "container-config"]):
            with patch("tools.security_gate.shutil.which", return_value=None):
                with self.assertRaisesRegex(SystemExit, "trivy"):
                    security_gate.main()


if __name__ == "__main__":
    unittest.main()
