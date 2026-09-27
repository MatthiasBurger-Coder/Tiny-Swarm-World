import stat
import tempfile
import unittest
from pathlib import Path

from tiny_swarm_world.domain.configuration.internal_test_credentials import internal_test_catalog
from tiny_swarm_world.infrastructure.adapters.configuration import ShellEnvFileConfigurationSource
from tools.create_internal_test_env_file import create_internal_test_env_file


class TestCreateInternalTestEnvFile(unittest.TestCase):
    def test_creates_protected_file_with_active_catalog_values(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            parent = Path(temporary_dir) / "credentials"
            parent.mkdir(mode=0o700)
            path = parent / "live-installation.env"

            self.assertTrue(create_internal_test_env_file(path))

            self.assertEqual(0o600, stat.S_IMODE(path.stat().st_mode))
            values = ShellEnvFileConfigurationSource(path).load()
            expected = {
                definition.key: definition.value
                for definition in internal_test_catalog().definitions
                if definition.active and definition.required
            }
            self.assertEqual(expected, values)

    def test_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            parent = Path(temporary_dir) / "credentials"
            parent.mkdir(mode=0o700)
            path = parent / "live-installation.env"
            path.write_text("TSW_PORTAINER_ADMIN_PASSWORD=operator-value\n", encoding="utf-8")
            path.chmod(0o600)

            self.assertFalse(create_internal_test_env_file(path))
            self.assertEqual(
                "TSW_PORTAINER_ADMIN_PASSWORD=operator-value\n",
                path.read_text(encoding="utf-8"),
            )

    def test_rejects_unprotected_parent(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            parent = Path(temporary_dir)
            parent.chmod(0o755)
            path = parent / "live-installation.env"
            with self.assertRaisesRegex(ValueError, "0700"):
                create_internal_test_env_file(path)
            self.assertFalse(path.exists())

    def test_rejects_symlinked_target(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            parent = Path(temporary_dir) / "credentials"
            parent.mkdir(mode=0o700)
            target = parent / "target.env"
            target.write_text("preserved\n", encoding="utf-8")
            path = parent / "live-installation.env"
            path.symlink_to(target)

            with self.assertRaisesRegex(ValueError, "symbolic links"):
                create_internal_test_env_file(path)
            self.assertEqual("preserved\n", target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
