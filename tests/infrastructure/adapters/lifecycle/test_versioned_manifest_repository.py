"""Isolated staging CAS safety and strict parser tests."""
from __future__ import annotations

import multiprocessing
import os
from pathlib import Path
import stat
import tempfile
from typing import cast
import unittest
from unittest.mock import patch

from tests.domain.lifecycle.test_scoped_route_policy import make_fixture
from tiny_swarm_world.application.ports.lifecycle.versioned_manifest import (
    ABSENT_TOKEN, CasToken, ReadStatus, TokenKind, WriteStatus,
)
from tiny_swarm_world.domain.lifecycle.manifest_v2_record import create_v2_record, encode_v2_record
from tiny_swarm_world.domain.lifecycle.scoped_route_policy import SwaggerMode
from tiny_swarm_world.infrastructure.adapters.lifecycle import versioned_manifest_repository as adapter


def concurrent_write(root: str, manifest: object, catalog: object, token: CasToken, queue: object) -> None:
    record = create_v2_record(manifest, catalog, exposure=SwaggerMode.NOT_APPLICABLE, listen_address="127.0.0.1")
    result = adapter.VersionedManifestStagingRepository(Path(root)).compare_and_swap(
        record, token, catalog, SwaggerMode.NOT_APPLICABLE, "127.0.0.1")  # type: ignore[arg-type]
    queue.put(result.status.value)  # type: ignore[attr-defined]


def controlled_crash(root: str, manifest: object, catalog: object, token: CasToken, phase: str) -> None:
    record = create_v2_record(manifest, catalog, exposure=SwaggerMode.NOT_APPLICABLE, listen_address="127.0.0.1")
    repository = adapter.VersionedManifestStagingRepository(Path(root))
    original = os.replace

    def replace_or_crash(*args: object, **kwargs: object) -> None:
        if phase == "before":
            os._exit(31)
        original(*args, **kwargs)  # type: ignore[arg-type]
        os._exit(32)

    with patch("os.replace", side_effect=replace_or_crash):
        repository.compare_and_swap(record, token, catalog, SwaggerMode.NOT_APPLICABLE, "127.0.0.1")  # type: ignore[arg-type]
    os._exit(33)


class VersionedStagingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest, self.catalog = make_fixture()
        self.repo = adapter.VersionedManifestStagingRepository(self.root)
        self.record = create_v2_record(self.manifest, self.catalog, exposure=SwaggerMode.NOT_APPLICABLE,
                                       listen_address="127.0.0.1")
        self.path = self.root / ".tiny-swarm-world" / "staging" / "manifest-v2-draft.json"
        self.lock = self.path.with_suffix(".lock")

    def read(self):
        return self.repo.read(self.catalog, SwaggerMode.NOT_APPLICABLE, "127.0.0.1")

    def write(self, record, token):
        return self.repo.compare_and_swap(record, token, self.catalog, SwaggerMode.NOT_APPLICABLE, "127.0.0.1")

    def test_absent_read_creates_nothing_and_create_noop_conflict(self) -> None:
        initial = self.read()
        self.assertIs(initial.status, ReadStatus.ABSENT)
        self.assertEqual(initial.token, ABSENT_TOKEN)
        self.assertEqual(list(self.root.iterdir()), [])
        created = self.write(self.record, ABSENT_TOKEN)
        self.assertIs(created.status, WriteStatus.SUCCESS)
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)
        before_inode = self.path.stat().st_ino
        same = self.write(self.record, created.token)
        self.assertIs(same.status, WriteStatus.SUCCESS)
        self.assertEqual(self.path.stat().st_ino, before_inode)
        self.assertIs(self.write(self.record, ABSENT_TOKEN).status, WriteStatus.CONFLICT)
        self.assertIs(self.read().status, ReadStatus.PRESENT)
        for item in (created, created.token, self.read(), self.record):
            self.assertNotIn("SECRET", repr(item))
            self.assertNotIn("12345678", str(item))

    def test_different_records_same_token_one_success_other_conflict(self) -> None:
        initial = self.write(self.record, ABSENT_TOKEN)
        first = create_v2_record(self.manifest.model_copy(update={"operation_reference": "first"}), self.catalog,
                                 exposure=SwaggerMode.NOT_APPLICABLE, listen_address="127.0.0.1")
        second = create_v2_record(self.manifest.model_copy(update={"operation_reference": "second"}), self.catalog,
                                  exposure=SwaggerMode.NOT_APPLICABLE, listen_address="127.0.0.1")
        self.assertIs(self.write(first, initial.token).status, WriteStatus.SUCCESS)
        self.assertIs(self.write(second, initial.token).status, WriteStatus.CONFLICT)

    def test_concurrent_processes_share_stable_lock_and_only_one_wins(self) -> None:
        initial = self.write(self.record, ABSENT_TOKEN)
        context = multiprocessing.get_context("fork")
        queue = context.Queue()
        processes = [context.Process(target=concurrent_write, args=(str(self.root),
                     self.manifest.model_copy(update={"operation_reference": name}),
                     self.catalog, initial.token, queue)) for name in ("first", "second")]
        for process in processes:
            process.start()
        for process in processes:
            process.join(timeout=15)
            self.assertEqual(process.exitcode, 0)
        outcomes = [queue.get(timeout=2), queue.get(timeout=2)]
        self.assertEqual(sorted(outcomes), ["CONFLICT", "SUCCESS"])
        self.assertEqual(self.lock.stat().st_nlink, 1)

    def test_byte_identical_aba_and_catalog_drift_limit(self) -> None:
        initial = self.write(self.record, ABSENT_TOKEN)
        original_bytes = self.path.read_bytes()
        changed = create_v2_record(self.manifest.model_copy(update={"operation_reference": "changed"}), self.catalog,
                                   exposure=SwaggerMode.NOT_APPLICABLE, listen_address="127.0.0.1")
        newer = self.write(changed, initial.token)
        self.assertIs(newer.status, WriteStatus.SUCCESS)
        restored = self.write(self.record, newer.token)
        self.assertIs(restored.status, WriteStatus.SUCCESS)
        self.assertEqual(self.path.read_bytes(), original_bytes)
        self.assertEqual(restored.token, initial.token)
        self.assertIs(self.write(self.record, initial.token).status, WriteStatus.SUCCESS)
        altered = self.catalog.model_copy(update={"catalog_version": 2})
        self.assertIs(self.repo.read(altered, SwaggerMode.NOT_APPLICABLE, "127.0.0.1").status, ReadStatus.BLOCKED)
        self.assertEqual(self.path.read_bytes(), original_bytes)

    def test_p1_v2_drafts_roundtrip_and_changed_inputs_block(self) -> None:
        for selected, has_8086 in ((("infisical",), False),
                                   (("service-access", "nexus", "infisical", "traefik"), True)):
            with self.subTest(selected=selected), tempfile.TemporaryDirectory() as directory:
                manifest, catalog = make_fixture(selected, "service-access")
                record = create_v2_record(manifest, catalog, exposure=SwaggerMode.NOT_APPLICABLE,
                                          listen_address="127.0.0.1")
                repo = adapter.VersionedManifestStagingRepository(Path(directory))
                result = repo.compare_and_swap(record, ABSENT_TOKEN, catalog,
                                              SwaggerMode.NOT_APPLICABLE, "127.0.0.1")
                self.assertIs(result.status, WriteStatus.SUCCESS)
                loaded = repo.read(catalog, SwaggerMode.NOT_APPLICABLE, "127.0.0.1")
                self.assertIs(loaded.status, ReadStatus.PRESENT)
                wire = loaded.record.wire()  # type: ignore[union-attr]
                desired = cast(dict[str, object], wire["desired"])
                ports = [row["listen_port"] for row in cast(list[dict[str, object]], desired["routes"])]
                self.assertEqual(8086 in ports, has_8086)
                self.assertIn(17080, ports)
                self.assertIs(repo.read(catalog, SwaggerMode.NOT_APPLICABLE, "0.0.0.0").status, ReadStatus.BLOCKED)

    def test_v1_read_and_invalid_data_do_not_rewrite(self) -> None:
        self.path.parent.parent.mkdir(mode=0o700)
        self.path.parent.mkdir(mode=0o700)
        self.path.write_text(self.manifest.model_dump_json(), encoding="utf-8")
        self.path.chmod(0o600)
        before = self.path.read_bytes()
        loaded = self.read()
        self.assertIs(loaded.status, ReadStatus.PRESENT)
        self.assertEqual(loaded.record, self.manifest)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse(self.lock.exists())

    def test_unsafe_links_modes_nonregular_and_missing_root_are_blocked(self) -> None:
        self.path.parent.parent.mkdir(mode=0o700)
        self.path.parent.mkdir(mode=0o700)
        victim = self.root / "victim"
        victim.write_bytes(b"SECRET")
        self.path.symlink_to(victim)
        self.assertIs(self.read().status, ReadStatus.BLOCKED)
        self.assertIs(self.write(self.record, ABSENT_TOKEN).status, WriteStatus.BLOCKED)
        self.path.unlink()
        os.link(victim, self.path)
        self.path.chmod(0o600)
        self.assertIs(self.read().status, ReadStatus.BLOCKED)
        self.path.unlink()
        victim.unlink()
        os.mkfifo(self.path, 0o600)
        self.assertIs(self.read().status, ReadStatus.BLOCKED)
        self.path.unlink()
        self.path.write_bytes(b"SECRET")
        self.path.chmod(0o644)
        self.assertIs(self.read().status, ReadStatus.BLOCKED)
        self.root.chmod(0o755)
        self.assertIs(self.read().status, ReadStatus.BLOCKED)
        self.root.chmod(0o700)
        missing = adapter.VersionedManifestStagingRepository(self.root / "missing")
        self.assertIs(missing.read(self.catalog, SwaggerMode.NOT_APPLICABLE, "127.0.0.1").status, ReadStatus.BLOCKED)

    def test_symlinked_staging_and_unsafe_lock_are_blocked(self) -> None:
        state = self.root / ".tiny-swarm-world"
        state.mkdir(mode=0o700)
        outside = self.root / "outside"
        outside.mkdir(mode=0o700)
        (state / "staging").symlink_to(outside, target_is_directory=True)
        self.assertIs(self.read().status, ReadStatus.BLOCKED)
        self.assertIs(self.write(self.record, ABSENT_TOKEN).status, WriteStatus.BLOCKED)
        (state / "staging").unlink()
        (state / "staging").mkdir(mode=0o700)
        self.lock.symlink_to(outside / "secret")
        self.assertIs(self.write(self.record, ABSENT_TOKEN).status, WriteStatus.BLOCKED)

    def test_pre_replace_failure_preserves_old_and_post_replace_is_uncertain(self) -> None:
        initial = self.write(self.record, ABSENT_TOKEN)
        before = self.path.read_bytes()
        changed = create_v2_record(self.manifest.model_copy(update={"operation_reference": "next"}), self.catalog,
                                   exposure=SwaggerMode.NOT_APPLICABLE, listen_address="127.0.0.1")
        with patch("os.fsync", side_effect=OSError("SECRET")):
            self.assertIs(self.write(changed, initial.token).status, WriteStatus.BLOCKED)
        self.assertEqual(self.path.read_bytes(), before)
        real_fsync = os.fsync
        real_replace = os.replace
        replaced = False
        def observe_replace(*args: object, **kwargs: object) -> None:
            nonlocal replaced
            real_replace(*args, **kwargs)  # type: ignore[arg-type]
            replaced = True
        def fail_directory(fd: int) -> None:
            if replaced and stat.S_ISDIR(os.fstat(fd).st_mode):
                raise OSError("SECRET")
            real_fsync(fd)
        with patch("os.replace", side_effect=observe_replace), patch("os.fsync", side_effect=fail_directory):
            outcome = self.write(changed, initial.token)
        self.assertIs(outcome.status, WriteStatus.UNCERTAIN)
        self.assertIsNone(outcome.token)
        self.assertIn(self.path.read_bytes(), (before, encode_v2_record(changed)))
        self.assertIs(self.read().status, ReadStatus.PRESENT)

    def test_uncertain_replace_same_bytes_requires_file_and_staging_fsync(self) -> None:
        initial = self.write(self.record, ABSENT_TOKEN)
        changed = create_v2_record(self.manifest.model_copy(update={"operation_reference": "next"}),
                                   self.catalog, exposure=SwaggerMode.NOT_APPLICABLE,
                                   listen_address="127.0.0.1")
        real_fsync, real_replace = os.fsync, os.replace
        replaced = False
        def track_replace(*args: object, **kwargs: object) -> None:
            nonlocal replaced
            real_replace(*args, **kwargs)  # type: ignore[arg-type]
            replaced = True
        def fail_post_replace_directory(fd: int) -> None:
            if replaced and stat.S_ISDIR(os.fstat(fd).st_mode):
                raise OSError("SECRET")
            real_fsync(fd)
        with patch("os.replace", side_effect=track_replace), patch("os.fsync", side_effect=fail_post_replace_directory):
            uncertain = self.write(changed, initial.token)
        self.assertIs(uncertain.status, WriteStatus.UNCERTAIN)
        observed = self.read()
        self.assertIs(observed.status, ReadStatus.PRESENT)
        staging_inode = self.path.parent.stat().st_ino
        def fail_staging(fd: int) -> None:
            if stat.S_ISDIR(os.fstat(fd).st_mode) and os.fstat(fd).st_ino == staging_inode:
                raise OSError("SECRET")
            real_fsync(fd)
        with patch("os.fsync", side_effect=fail_staging):
            self.assertIs(self.write(changed, observed.token).status, WriteStatus.BLOCKED)
        def fail_file(fd: int) -> None:
            if stat.S_ISREG(os.fstat(fd).st_mode):
                raise OSError("SECRET")
            real_fsync(fd)
        with patch("os.fsync", side_effect=fail_file):
            self.assertIs(self.write(changed, observed.token).status, WriteStatus.BLOCKED)
        self.assertIs(self.write(changed, observed.token).status, WriteStatus.SUCCESS)

    def test_new_directory_parent_fsync_failures_block_before_replace(self) -> None:
        for fail_on in (1, 2):
            with self.subTest(fail_on=fail_on), tempfile.TemporaryDirectory() as directory:
                repository = adapter.VersionedManifestStagingRepository(Path(directory))
                real_fsync = os.fsync
                directory_calls = 0
                def fail_nth_directory(fd: int) -> None:
                    nonlocal directory_calls
                    if stat.S_ISDIR(os.fstat(fd).st_mode):
                        directory_calls += 1
                        if directory_calls == fail_on:
                            raise OSError("SECRET")
                    real_fsync(fd)
                with patch("os.fsync", side_effect=fail_nth_directory):
                    result = repository.compare_and_swap(self.record, ABSENT_TOKEN, self.catalog,
                                                         SwaggerMode.NOT_APPLICABLE, "127.0.0.1")
                self.assertIs(result.status, WriteStatus.BLOCKED)
                self.assertFalse((Path(directory) / ".tiny-swarm-world/staging/manifest-v2-draft.json").exists())

    def test_retry_must_sync_a_previously_created_unsynced_parent(self) -> None:
        root_inode = self.root.stat().st_ino
        real_fsync = os.fsync
        def fail_root(fd: int) -> None:
            if os.fstat(fd).st_ino == root_inode:
                raise OSError("SECRET")
            real_fsync(fd)
        for _ in range(2):
            with patch("os.fsync", side_effect=fail_root):
                result = self.write(self.record, ABSENT_TOKEN)
            self.assertIs(result.status, WriteStatus.BLOCKED)
            self.assertFalse(self.path.exists())
        self.assertTrue((self.root / ".tiny-swarm-world").is_dir())
        self.assertIs(self.write(self.record, ABSENT_TOKEN).status, WriteStatus.SUCCESS)

    def test_concurrent_existing_directory_is_parent_synced(self) -> None:
        root_inode = self.root.stat().st_ino
        actual_mkdir, actual_fsync = os.mkdir, os.fsync
        synced: list[int] = []
        raced = False
        def racing_mkdir(path: object, mode: int = 0o777, *, dir_fd: int | None = None) -> None:
            nonlocal raced
            if path == ".tiny-swarm-world" and not raced:
                raced = True
                actual_mkdir(path, mode, dir_fd=dir_fd)  # type: ignore[arg-type]
                raise FileExistsError
            actual_mkdir(path, mode, dir_fd=dir_fd)  # type: ignore[arg-type]
        def record_fsync(fd: int) -> None:
            synced.append(os.fstat(fd).st_ino)
            actual_fsync(fd)
        with patch("os.mkdir", side_effect=racing_mkdir), patch("os.fsync", side_effect=record_fsync):
            result = self.write(self.record, ABSENT_TOKEN)
        self.assertIs(result.status, WriteStatus.SUCCESS)
        self.assertTrue(raced)
        self.assertIn(root_inode, synced)
        self.assertIn((self.root / ".tiny-swarm-world").stat().st_ino, synced)

    def test_lock_replacement_at_each_binding_check_blocks_before_commit(self) -> None:
        for replacement_check in (1, 2, 3):
            with self.subTest(replacement_check=replacement_check):
                self.setUp()
                initial = self.write(self.record, ABSENT_TOKEN)
                before = self.path.read_bytes()
                changed = create_v2_record(self.manifest.model_copy(update={"operation_reference": "next"}),
                                           self.catalog, exposure=SwaggerMode.NOT_APPLICABLE,
                                           listen_address="127.0.0.1")
                original_check = self.repo._check_lock
                calls = 0
                def retarget(parent, lock, identity):
                    nonlocal calls
                    calls += 1
                    if calls == replacement_check:
                        self.lock.rename(self.lock.with_name("displaced.lock"))
                        self.lock.write_bytes(b"")
                        self.lock.chmod(0o600)
                    return original_check(parent, lock, identity)
                with patch.object(self.repo, "_check_lock", side_effect=retarget):
                    result = self.write(changed, initial.token)
                self.assertIs(result.status, WriteStatus.BLOCKED)
                self.assertEqual(self.path.read_bytes(), before)

    def test_write_and_replace_failures_preserve_old_with_correct_classification(self) -> None:
        initial = self.write(self.record, ABSENT_TOKEN)
        before = self.path.read_bytes()
        changed = create_v2_record(self.manifest.model_copy(update={"operation_reference": "next"}),
                                   self.catalog, exposure=SwaggerMode.NOT_APPLICABLE,
                                   listen_address="127.0.0.1")
        with patch("os.write", side_effect=OSError("SECRET")):
            self.assertIs(self.write(changed, initial.token).status, WriteStatus.BLOCKED)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.glob(".manifest-v2-*.tmp")), [])
        with patch("os.replace", side_effect=OSError("SECRET")):
            self.assertIs(self.write(changed, initial.token).status, WriteStatus.UNCERTAIN)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.glob(".manifest-v2-*.tmp")), [])
        self.assertIs(self.read().status, ReadStatus.PRESENT)

    def test_close_error_after_replace_is_uncertain_without_partial_result(self) -> None:
        initial = self.write(self.record, ABSENT_TOKEN)
        changed = create_v2_record(self.manifest.model_copy(update={"operation_reference": "next"}),
                                   self.catalog, exposure=SwaggerMode.NOT_APPLICABLE,
                                   listen_address="127.0.0.1")
        original_close = os.close
        original_replace = os.replace
        replaced = False
        def observe_replace(*args: object, **kwargs: object) -> None:
            nonlocal replaced
            original_replace(*args, **kwargs)  # type: ignore[arg-type]
            replaced = True
        def close_or_fail(fd: int) -> None:
            try:
                name = os.readlink(f"/proc/self/fd/{fd}")
            except OSError:
                name = ""
            original_close(fd)
            if replaced and name.endswith("manifest-v2-draft.json"):
                raise OSError("SECRET")
        with patch("os.replace", side_effect=observe_replace), patch("os.close", side_effect=close_or_fail):
            result = self.write(changed, initial.token)
        self.assertIs(result.status, WriteStatus.UNCERTAIN)
        self.assertIsNone(result.token)
        self.assertIs(self.read().status, ReadStatus.PRESENT)

    def test_real_child_crash_before_and_after_replace_reconciles_read_only(self) -> None:
        for phase, expected_exit in (("before", 31), ("after", 32)):
            with self.subTest(phase=phase):
                self.setUp()
                initial = self.write(self.record, ABSENT_TOKEN)
                before = self.path.read_bytes()
                changed_manifest = self.manifest.model_copy(update={"operation_reference": "next"})
                changed = create_v2_record(changed_manifest, self.catalog, exposure=SwaggerMode.NOT_APPLICABLE,
                                           listen_address="127.0.0.1")
                context = multiprocessing.get_context("fork")
                process = context.Process(target=controlled_crash,
                                          args=(str(self.root), changed_manifest, self.catalog, initial.token, phase))
                process.start()
                process.join(timeout=15)
                self.assertEqual(process.exitcode, expected_exit)
                after = self.path.read_bytes()
                if phase == "before":
                    self.assertEqual(after, before)
                else:
                    self.assertIn(after, (before, encode_v2_record(changed)))
                self.assertIs(self.read().status, ReadStatus.PRESENT)

    def test_bounded_json_and_nested_duplicates_are_blocked(self) -> None:
        self.path.parent.parent.mkdir(mode=0o700)
        self.path.parent.mkdir(mode=0o700)
        cases = (
            b"", b"{}", b'{"schema_version":true}',
            b'{"schema_version":2,"v1":{"a":1,"a":2}}',
            b'{"schema_version":2,"x":NaN}', b'{"schema_version":2,"x":Infinity}',
            b'{"schema_version":2,"x":-Infinity}', b'{"schema_version":2,"x":1e999}',
            b"[" * 33 + b"0" + b"]" * 33,
            b"[" + b"0," * 50000 + b"0]",
            b"x" * (1024 * 1024 + 1), b"\xff",
        )
        for raw in cases:
            with self.subTest(size=len(raw), first=raw[:20]):
                self.path.write_bytes(raw)
                self.path.chmod(0o600)
                before = self.path.read_bytes()
                self.assertIs(self.read().status, ReadStatus.BLOCKED)
                self.assertEqual(self.path.read_bytes(), before)

    def test_invalid_tokens_and_inputs_never_leak(self) -> None:
        with self.assertRaises(ValueError):
            CasToken(TokenKind.PRESENT, "SECRET")
        token = CasToken(TokenKind.PRESENT, "a" * 64)
        self.assertNotIn("a" * 64, repr(token))
        self.assertIs(self.write(self.record, None).status, WriteStatus.BLOCKED)
        self.assertEqual(list(self.root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
