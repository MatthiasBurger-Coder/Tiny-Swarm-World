import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from tests.support.sonar_safe_literals import operator_credential

from tiny_swarm_world.infrastructure.adapters.file_management.file_manager import FileManager
from tiny_swarm_world.infrastructure.adapters.file_management.local_file_storage import (
    LocalFileStorage,
)


class TestFileManager(unittest.TestCase):
    def test_save_logs_path_without_file_contents(self):
        manager = object.__new__(FileManager)
        manager.logger = MagicMock()
        saver = MagicMock()
        manager.saver = lambda _path: saver
        path = Path("local-state.env")
        value = operator_credential()

        manager.save(path, value)

        saver.save.assert_called_once_with(value)
        manager.logger.info.assert_called_once_with("Saving file: %s", path)
        self.assertNotIn(value, str(manager.logger.info.call_args))

    def test_local_storage_writes_private_state_with_owner_only_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private" / "state.env"

            LocalFileStorage().write_text(path, "safe-placeholder\n", private=True)

            self.assertEqual("safe-placeholder\n", path.read_text(encoding="utf-8"))
            self.assertEqual(0o600, path.stat().st_mode & 0o777)
            self.assertEqual(0o700, path.parent.stat().st_mode & 0o777)
            self.assertEqual([], list(path.parent.glob(f".{path.name}.*")))


if __name__ == "__main__":
    unittest.main()
