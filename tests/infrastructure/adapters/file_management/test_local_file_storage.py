import traceback
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tiny_swarm_world.application.ports.operation_result import OperationError
from tiny_swarm_world.infrastructure.adapters.file_management.local_file_storage import LocalFileStorage


class TestLocalFileStorage(unittest.TestCase):
    def test_private_atomic_roundtrip_and_missing_default(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "private" / "value.txt"
            storage = LocalFileStorage()
            self.assertIsNone(storage.read_text(path))
            storage.write_text(path, "value", private=True)
            self.assertEqual("value", storage.read_text(path))
            self.assertEqual(0o600, path.stat().st_mode & 0o777)
            self.assertEqual(0o700, path.parent.stat().st_mode & 0o777)
            self.assertEqual([path], list(path.parent.iterdir()))

    def test_io_errors_keep_oserror_contract_and_suppress_diagnostics(self):
        marker = "sensitive-storage-payload"
        storage = LocalFileStorage()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "file.txt"
            path.write_text("original", encoding="utf-8")
            for method, action in (
                ("read_text", lambda: storage.read_text(path)),
                ("mkdir", lambda: storage.ensure_directory(path.parent)),
                ("replace", lambda: storage.write_text(path, "replacement")),
                ("chmod", lambda: storage.ensure_directory(path.parent, private=True)),
            ):
                with self.subTest(method=method), patch.object(Path, method, side_effect=OSError(marker)):
                    try:
                        action()
                    except OperationError as error:
                        self.assertIsInstance(error, OSError)
                        self.assertEqual("filesystem_error", error.failure.cause)
                        self.assertNotIn(marker, "".join(traceback.format_exception(error)))
                        self.assertNotIn(marker, repr(error))
                        self.assertNotIn(marker, str(error.failure.to_dict()))
                    else:
                        self.fail("Expected a declared storage failure")
            self.assertEqual("original", path.read_text(encoding="utf-8"))
            self.assertEqual([path], list(path.parent.iterdir()))

    def test_cleanup_failure_is_also_classified(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "value.txt"
            with patch.object(Path, "replace", side_effect=OSError("write-private")), patch.object(Path, "unlink", side_effect=OSError("cleanup-private")):
                with self.assertRaises(OperationError) as caught:
                    LocalFileStorage().write_text(path, "value")
            self.assertIsInstance(caught.exception, OSError)
            self.assertEqual("filesystem_error", caught.exception.failure.cause)
            self.assertTrue(caught.exception.__suppress_context__)

    def test_failed_cleanup_preserves_control_flow_and_primary_typed_failure(self):
        import asyncio
        from tiny_swarm_world.application.ports.operation_result import OperationFailure
        from tiny_swarm_world.application.ports.file_management.port_local_file_storage import LocalFileStorageError
        typed = LocalFileStorageError(OperationFailure.for_cause("original.write", "original", "filesystem_error"))
        for primary in (asyncio.CancelledError(), KeyboardInterrupt(), SystemExit(), typed):
            with self.subTest(primary=type(primary)), TemporaryDirectory() as directory:
                path = Path(directory) / "value.txt"
                with patch.object(Path, "replace", side_effect=primary), patch.object(Path, "unlink", side_effect=OSError("cleanup-private")):
                    with self.assertRaises(type(primary)) as caught:
                        LocalFileStorage().write_text(path, "value")
                self.assertIs(primary, caught.exception)

    def test_scan_does_not_report_empty_success_when_scandir_is_denied(self):
        with TemporaryDirectory() as directory:
            with patch("os.scandir", side_effect=PermissionError("private-scan")):
                with self.assertRaises(OperationError) as caught:
                    LocalFileStorage().scan_text_files(Path(directory), suffixes=frozenset({".txt"}), skip_parts=frozenset())
            self.assertEqual("storage.scan", caught.exception.failure.operation)
            self.assertEqual("filesystem_error", caught.exception.failure.cause)
