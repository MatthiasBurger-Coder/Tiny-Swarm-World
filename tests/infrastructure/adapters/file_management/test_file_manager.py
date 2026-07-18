import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

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

            self.assertEqual(path.read_text(encoding="utf-8"), "safe-placeholder\n")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)
            self.assertEqual(list(path.parent.glob(f".{path.name}.*")), [])

    def test_local_storage_prunes_skipped_trees_before_scanning(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_root = root / "src"
            source_root.mkdir()
            expected_path = source_root / "settings.yaml"
            expected_path.write_text("value: placeholder\n", encoding="utf-8")
            observed_directories: list[tuple[str, ...]] = []

            def controlled_walk(path, *, topdown):
                self.assertEqual(root, path)
                self.assertTrue(topdown)
                directory_names = ["src", ".tiny-swarm-world", ".git"]
                yield str(root), directory_names, []
                observed_directories.append(tuple(directory_names))
                if "src" in directory_names:
                    yield str(source_root), [], [expected_path.name]
                if ".tiny-swarm-world" in directory_names or ".git" in directory_names:
                    self.fail("scanner descended into an excluded local-state tree")

            with patch(
                "tiny_swarm_world.infrastructure.adapters.file_management.local_file_storage.os.walk",
                side_effect=controlled_walk,
            ):
                snapshots = LocalFileStorage().scan_text_files(
                    root,
                    suffixes=frozenset({".yaml"}),
                    skip_parts=frozenset({".git", ".tiny-swarm-world"}),
                )

            self.assertEqual(observed_directories, [("src",)])
            self.assertEqual(tuple(item.path for item in snapshots), (expected_path,))


if __name__ == "__main__":
    unittest.main()
