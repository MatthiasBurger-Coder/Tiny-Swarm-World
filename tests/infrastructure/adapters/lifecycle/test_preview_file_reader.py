"""Bounded fixed-path reader tests; no runtime host operations."""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tiny_swarm_world.infrastructure.adapters.lifecycle import preview_file_reader as reader


class PreviewFileReaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for relative in reader.ALLOWED:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"example")

    def test_exact_ten_fixed_paths_and_no_duplicate_reads(self) -> None:
        self.assertEqual(len(reader.COMPOSE_FILES), 9)
        self.assertEqual(len(reader.ALLOWED), 10)
        with reader.PreviewFileReader(self.root) as source:
            for path in sorted(reader.ALLOWED):
                self.assertEqual(source.read(path), b"example")
            with self.assertRaises(ValueError):
                source.read(reader.MANIFEST)

    def test_arbitrary_paths_are_rejected_without_reads(self) -> None:
        with reader.PreviewFileReader(self.root) as source:
            for path in ("../secret", "/private/secret", "", "infra//config", "infra/./config", "private"):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    source.read(path)

    def test_symlinks_in_final_and_directory_components_are_rejected(self) -> None:
        target = self.root / reader.MANIFEST
        target.unlink()
        target.symlink_to(self.root / next(iter(reader.COMPOSE_FILES)))
        with self.assertRaises(OSError), reader.PreviewFileReader(self.root) as source:
            source.read(reader.MANIFEST)
        target.unlink()
        target.parent.rmdir()
        target.parent.symlink_to(self.root / "infra", target_is_directory=True)
        with self.assertRaises(OSError), reader.PreviewFileReader(self.root) as source:
            source.read(reader.MANIFEST)

    def test_nonregular_fifo_does_not_block(self) -> None:
        path = self.root / reader.MANIFEST
        path.unlink()
        os.mkfifo(path)
        with self.assertRaises(ValueError), reader.PreviewFileReader(self.root) as source:
            source.read(reader.MANIFEST)

    def test_exact_file_limit_and_short_chunks_are_read_without_truncation(self) -> None:
        path = self.root / reader.MANIFEST
        expected = b"0123456789abcdef" * (reader.MAX_FILE_BYTES // 16)
        path.write_bytes(expected)
        real_read = os.read
        def short_read(fd: int, size: int) -> bytes:
            return real_read(fd, min(size, 8191))
        with patch("os.read", side_effect=short_read), reader.PreviewFileReader(self.root) as source:
            self.assertEqual(source.read(reader.MANIFEST), expected)

    def test_file_total_and_count_limits_fail_closed(self) -> None:
        path = self.root / reader.MANIFEST
        path.write_bytes(b"x" * (reader.MAX_FILE_BYTES + 1))
        with self.assertRaises(ValueError), reader.PreviewFileReader(self.root) as source:
            source.read(reader.MANIFEST)
        path.write_bytes(b"abcd")
        # Lowered limits exercise otherwise unreachable aggregate/count boundaries.
        with patch.object(reader, "MAX_TOTAL_BYTES", 3), \
                self.assertRaises(ValueError), reader.PreviewFileReader(self.root) as source:
            source.read(reader.MANIFEST)
        with patch.object(reader, "MAX_FILES", 1), \
                self.assertRaises(ValueError), reader.PreviewFileReader(self.root) as source:
            source.read(reader.MANIFEST)
            source.read(next(iter(reader.COMPOSE_FILES)))

    def test_short_read_and_path_replacement_fail_closed(self) -> None:
        with patch("os.read", return_value=b""), \
                self.assertRaises(ValueError), reader.PreviewFileReader(self.root) as source:
            source.read(reader.MANIFEST)
        path = self.root / reader.MANIFEST
        with self.assertRaises((ValueError, OSError)), reader.PreviewFileReader(self.root) as source:
            source.read(reader.MANIFEST)
            path.rename(path.with_name("old"))
            path.write_bytes(b"example")

    def test_permission_missing_and_unexpected_stack_set_fail_closed(self) -> None:
        with patch("os.open", side_effect=PermissionError("SECRET")), self.assertRaises(PermissionError):
            with reader.PreviewFileReader(self.root):
                pass
        (self.root / reader.MANIFEST).unlink()
        with self.assertRaises(FileNotFoundError), reader.PreviewFileReader(self.root) as source:
            source.read(reader.MANIFEST)
        with patch.object(reader, "STACK_IDS", frozenset({"unknown"})), self.assertRaises(ValueError):
            with reader.PreviewFileReader(self.root):
                pass

    def test_all_open_failures_close_previously_pinned_fds(self) -> None:
        for failed_call in range(1, 5):
            with self.subTest(failed_call=failed_call):
                before = set(os.listdir("/proc/self/fd"))
                real_open = os.open
                calls = 0
                def fail_once(*args: object, **kwargs: object) -> int:
                    nonlocal calls
                    calls += 1
                    if calls == failed_call:
                        raise PermissionError("private")
                    return real_open(*args, **kwargs)  # type: ignore[arg-type]
                with patch("os.open", side_effect=fail_once), self.assertRaises(PermissionError):
                    with reader.PreviewFileReader(self.root) as source:
                        source.read(reader.MANIFEST)
                self.assertEqual(set(os.listdir("/proc/self/fd")), before)

    def test_read_and_intermediate_fstat_failures_close_fds(self) -> None:
        before = set(os.listdir("/proc/self/fd"))
        with patch("os.read", side_effect=OSError("SECRET")), self.assertRaises(OSError):
            with reader.PreviewFileReader(self.root) as source:
                source.read(reader.MANIFEST)
        self.assertEqual(set(os.listdir("/proc/self/fd")), before)
        real_fstat = os.fstat
        calls = 0
        def failing_fstat(fd: int) -> os.stat_result:
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("SECRET")
            return real_fstat(fd)
        with patch("os.fstat", side_effect=failing_fstat), self.assertRaises(OSError):
            with reader.PreviewFileReader(self.root) as source:
                source.read(reader.MANIFEST)
        self.assertEqual(set(os.listdir("/proc/self/fd")), before)

    def test_post_read_metadata_drift_is_rejected(self) -> None:
        path = self.root / reader.MANIFEST
        with self.assertRaises(ValueError), reader.PreviewFileReader(self.root) as source:
            source.read(reader.MANIFEST)
            path.write_bytes(b"modified")

    def test_close_error_attempts_every_descriptor_once_without_retry(self) -> None:
        source = reader.PreviewFileReader(self.root)
        before = set(os.listdir("/proc/self/fd"))
        actual_close = os.close
        attempts: list[int] = []
        with self.assertRaisesRegex(OSError, r"^Preview descriptor cleanup failed\.$"):
            with source:
                source.read(reader.MANIFEST)
                expected = list(reversed(source._fds))
                def failing_close(fd: int) -> None:
                    attempts.append(fd)
                    actual_close(fd)
                    if len(attempts) == 2:
                        raise OSError("SECRET")
                with patch("os.close", side_effect=failing_close):
                    source.__exit__(None, None, None)
        self.assertEqual(attempts, expected)
        self.assertEqual(len(attempts), len(set(attempts)))
        self.assertEqual(set(os.listdir("/proc/self/fd")), before)

    def test_enter_and_recheck_failures_still_attempt_cleanup(self) -> None:
        actual_close = os.close
        closed: list[int] = []
        def close_then_fail(fd: int) -> None:
            closed.append(fd)
            actual_close(fd)
            raise OSError("SECRET")

        with patch("os.fstat", side_effect=PermissionError("SECRET")), \
                patch("os.close", side_effect=close_then_fail), self.assertRaisesRegex(
                    OSError, r"^Preview descriptor cleanup failed\.$"):
            with reader.PreviewFileReader(self.root):
                pass
        self.assertEqual(len(closed), 1)

        source = reader.PreviewFileReader(self.root)
        source.__enter__()
        source.read(reader.MANIFEST)
        expected = list(reversed(source._fds))
        closed.clear()
        with patch.object(source, "_recheck", side_effect=ValueError("SECRET")), \
                patch("os.close", side_effect=close_then_fail), self.assertRaisesRegex(
                    OSError, r"^Preview descriptor cleanup failed\.$"):
            source.__exit__(None, None, None)
        self.assertEqual(closed, expected)
        self.assertEqual(len(closed), len(set(closed)))

    def test_every_success_and_error_closes_descriptors(self) -> None:
        before = set(os.listdir("/proc/self/fd"))
        with reader.PreviewFileReader(self.root) as source:
            source.read(reader.MANIFEST)
        self.assertEqual(set(os.listdir("/proc/self/fd")), before)
        with self.assertRaises(ValueError), reader.PreviewFileReader(self.root) as source:
            source.read(reader.MANIFEST)
            source.read("../SECRET")
        self.assertEqual(set(os.listdir("/proc/self/fd")), before)


if __name__ == "__main__":
    unittest.main()
