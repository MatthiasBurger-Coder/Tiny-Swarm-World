"""Exercise real no-follow file policy on isolated unprivileged temporary trees."""
from __future__ import annotations

import asyncio
import json
import os
import signal
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from tiny_swarm_world.infrastructure.process import async_runner
from tiny_swarm_world.infrastructure.adapters.network_preparation import files
from tiny_swarm_world.infrastructure.adapters.network_preparation import privileged_files as helper


class ProtectedFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.target = self.root / "setting"

    def observation(self) -> dict:
        return helper.snapshot(self.target, anchor=self.root, uid=os.getuid(), gid=os.getgid())

    def publish(self, before: dict, payload: bytes, shared: bool = False) -> None:
        helper.publish(self.target, before, payload, before["mode"] if shared else 0o644,
                       shared, targets={str(self.target): None if shared else 0o644},
                       anchor=self.root, uid=os.getuid(), gid=os.getgid())

    def existing(self, content: bytes = b"prior\n") -> dict:
        self.target.write_bytes(content)
        self.target.chmod(0o644)
        return self.observation()

    def test_new_file_and_compatible_reuse_write_nothing(self) -> None:
        self.publish(self.observation(), b"new\n")
        before = self.observation()
        self.publish(before, b"new\n")
        self.assertEqual(before, self.observation())
        self.assertEqual([self.target], list(self.root.iterdir()))

    def test_incompatible_file_is_not_adopted(self) -> None:
        before = self.existing()
        with self.assertRaisesRegex(ValueError, "Incompatible"):
            self.publish(before, b"replaced")
        self.assertEqual(before, self.observation())
        self.assertEqual([self.target], list(self.root.iterdir()))

    def test_stale_content_mode_inode_and_missing_target(self) -> None:
        for change in ("content", "mode", "inode", "appeared"):
            with self.subTest(change=change):
                self.target.unlink(missing_ok=True)
                before = self.observation() if change == "appeared" else self.existing()
                if change == "mode":
                    self.target.chmod(0o600)
                elif change == "inode":
                    other = self.root / "other"
                    other.write_bytes(b"prior\n")
                    other.chmod(0o644)
                    other.replace(self.target)
                else:
                    self.target.write_bytes(b"different")
                with self.assertRaisesRegex(RuntimeError, "stale"):
                    self.publish(before, before["content"] or b"new")

    def test_symlink_hardlink_unsafe_mode_and_nonregular_rejected(self) -> None:
        self.target.symlink_to(self.root / "absent")
        with self.assertRaises(OSError):
            self.observation()
        self.target.unlink()
        self.existing()
        os.link(self.target, self.root / "link")
        with self.assertRaisesRegex(ValueError, "metadata"):
            self.observation()
        (self.root / "link").unlink()
        self.target.chmod(0o666)
        with self.assertRaises(ValueError):
            self.observation()
        self.target.unlink()
        os.mkfifo(self.target)
        with self.assertRaises(ValueError):
            self.observation()

    def test_unsafe_and_symlink_ancestors_rejected_without_writes(self) -> None:
        directory = self.root / "parent"
        directory.mkdir(mode=0o777)
        directory.chmod(0o777)
        self.target = directory / "setting"
        with self.assertRaises(ValueError):
            self.observation()
        directory.chmod(0o700)
        self.target = self.root / "symlink" / "setting"
        (self.root / "symlink").symlink_to(directory, target_is_directory=True)
        with self.assertRaises(OSError):
            self.observation()
        self.assertEqual([], list(directory.iterdir()))

    def test_identity_includes_ancestor_ownership_and_target_owner(self) -> None:
        self.existing()
        with self.assertRaises(ValueError):
            helper.snapshot(self.target, anchor=self.root, uid=os.getuid() + 1)
        with self.assertRaises(ValueError):
            helper.snapshot(self.target, anchor=self.root, uid=os.getuid(), gid=os.getgid() + 1)

    def test_hosts_change_preserves_bytes_metadata_and_protected_backup(self) -> None:
        original = b"127.0.0.1 localhost\r\n# private comment\r\n"
        before = self.existing(original)
        payload = files.desired_hosts(original, ("jenkins.local", "nexus.local"))
        self.publish(before, payload, shared=True)
        self.assertTrue(self.target.read_bytes().startswith(original))
        self.assertEqual(before["mode"], self.observation()["mode"])
        backups = [path for path in self.root.glob(".tsw-backup-*") if path.suffix != ".metadata"]
        self.assertEqual(1, len(backups))
        self.assertEqual(original, backups[0].read_bytes())
        self.assertEqual(0o600, backups[0].stat().st_mode & 0o777)
        self.assertEqual(1, backups[0].stat().st_nlink)
        metadata = backups[0].with_name(backups[0].name + ".metadata")
        self.assertEqual(before["mode"], json.loads(metadata.read_bytes())["mode"])
        self.assertEqual(0o600, metadata.stat().st_mode & 0o777)
        self.publish(self.observation(), payload, shared=True)
        self.assertEqual(backups, [path for path in self.root.glob(".tsw-backup-*") if path.suffix != ".metadata"])

    def test_backup_collision_blocks_before_publication(self) -> None:
        before = self.existing(b"127.0.0.1 localhost\n")
        backup = self.root / ".tsw-backup-hosts-collision"
        backup.write_bytes(b"do not replace")
        token = unittest.mock.Mock(hex="collision")
        with patch.object(helper.uuid, "uuid4", return_value=token):
            with self.assertRaises(FileExistsError):
                self.publish(before, files.desired_hosts(before["content"], ("jenkins.local",)), True)
        self.assertEqual(before, self.observation())
        self.assertEqual(b"do not replace", backup.read_bytes())

    def test_shared_update_cannot_change_unrelated_content(self) -> None:
        before = self.existing(b"127.0.0.1 localhost\n")
        payload = files.desired_hosts(before["content"], ("jenkins.local",))
        with self.assertRaisesRegex(ValueError, "unrelated"):
            self.publish(before, payload.replace(b"localhost", b"forged"), True)
        self.assertEqual(before, self.observation())

    def test_drift_before_atomic_publication_preserves_foreign_change(self) -> None:
        before = self.existing(b"127.0.0.1 localhost\n")
        payload = files.desired_hosts(before["content"], ("jenkins.local",))
        actual_write = helper._write_private

        def drift(*args, **kwargs):
            actual_write(*args, **kwargs)
            if str(args[1]).startswith(".tsw-write-"):
                self.target.write_bytes(b"foreign update\n")

        with patch.object(helper, "_write_private", side_effect=drift):
            with self.assertRaisesRegex(RuntimeError, "before publication"):
                self.publish(before, payload, True)
        self.assertEqual(b"foreign update\n", self.target.read_bytes())
        self.assertEqual([], list(self.root.glob(".tsw-write-*")))
        self.assertEqual(before["content"], next(path for path in self.root.glob(".tsw-backup-*") if path.suffix != ".metadata").read_bytes())

    def test_extended_attributes_block_without_adoption(self) -> None:
        self.existing()
        os.setxattr(self.target, "user.tsw-test", b"must preserve")
        with self.assertRaisesRegex(ValueError, "extended attributes"):
            self.observation()
        self.assertEqual(b"must preserve", os.getxattr(self.target, "user.tsw-test"))
        self.assertEqual([self.target], list(self.root.iterdir()))

    def test_parent_swap_blocks_publication_in_displaced_directory(self) -> None:
        parent = self.root / "parent"
        parent.mkdir(mode=0o700)
        self.target = parent / "setting"
        before = self.observation()
        displaced = self.root / "displaced"
        actual_write = helper._write_private

        def swap(*args, **kwargs):
            actual_write(*args, **kwargs)
            parent.rename(displaced)
            parent.mkdir(mode=0o700)

        with patch.object(helper, "_write_private", side_effect=swap):
            with self.assertRaisesRegex(RuntimeError, "before publication"):
                self.publish(before, b"new")
        self.assertFalse(self.target.exists())
        self.assertEqual([], list(displaced.iterdir()))

    def test_retained_parent_identity_is_checked(self) -> None:
        parent = self.root / "parent"
        parent.mkdir(mode=0o700)
        target = parent / "setting"
        fd, _ = helper._parent(target, self.root, os.getuid())
        try:
            parent.rename(self.root / "displaced")
            parent.mkdir(mode=0o700)
            with self.assertRaisesRegex(RuntimeError, "parent changed"):
                helper._check_parent(fd, target, self.root, os.getuid())
        finally:
            os.close(fd)

    def test_failed_atomic_replacement_cleans_temporary_and_retains_backup(self) -> None:
        before = self.existing(b"127.0.0.1 localhost\n")
        payload = files.desired_hosts(before["content"], ("jenkins.local",))
        with patch.object(helper.os, "replace", side_effect=OSError("publication failure")):
            with self.assertRaisesRegex(OSError, "publication failure"):
                self.publish(before, payload, True)
        self.assertEqual(before, self.observation())
        self.assertEqual([], list(self.root.glob(".tsw-write-*")))
        backups = [path for path in self.root.glob(".tsw-backup-*")
                   if path.suffix != ".metadata"]
        self.assertEqual(1, len(backups))
        self.assertEqual(before["content"], backups[0].read_bytes())
        self.assertTrue(backups[0].with_name(backups[0].name + ".metadata").exists())

    def test_failed_postcheck_preserves_attempted_effect_and_backup(self) -> None:
        for failure in ("observation_error", "unexpected_observation"):
            with self.subTest(failure=failure):
                before = self.existing(b"127.0.0.1 localhost\n")
                payload = files.desired_hosts(before["content"], ("jenkins.local",))
                snapshot = helper.snapshot
                calls = 0

                def observe(*args, **kwargs):
                    nonlocal calls
                    calls += 1
                    if calls == 3:
                        if failure == "observation_error":
                            raise OSError("postcheck observation unavailable")
                        return {**snapshot(*args, **kwargs), "content": b"unexpected"}
                    return snapshot(*args, **kwargs)

                with patch.object(helper, "snapshot", side_effect=observe):
                    with self.assertRaises((OSError, RuntimeError)):
                        self.publish(before, payload, True)
                self.assertEqual(payload, self.target.read_bytes())
                self.assertEqual([], list(self.root.glob(".tsw-write-*")))
                backups = [path for path in self.root.glob(".tsw-backup-*")
                           if path.suffix != ".metadata"]
                self.assertTrue(backups)
                self.assertTrue(all(path.read_bytes() == before["content"] for path in backups))

    def test_interruption_after_publication_keeps_effect_and_backup(self) -> None:
        before = self.existing(b"127.0.0.1 localhost\n")
        payload = files.desired_hosts(before["content"], ("jenkins.local",))
        replace = helper.os.replace

        def interrupted(*args, **kwargs):
            replace(*args, **kwargs)
            raise KeyboardInterrupt

        with patch.object(helper.os, "replace", side_effect=interrupted):
            with self.assertRaises(KeyboardInterrupt):
                self.publish(before, payload, True)
        self.assertEqual(payload, self.target.read_bytes())
        self.assertEqual([], list(self.root.glob(".tsw-write-*")))
        backup = next(path for path in self.root.glob(".tsw-backup-*")
                      if path.suffix != ".metadata")
        self.assertEqual(before["content"], backup.read_bytes())

    def test_real_production_allowlist_rejects_arbitrary_targets(self) -> None:
        with self.assertRaisesRegex(ValueError, "scope"):
            helper.publish(self.target, self.observation(), b"new", 0o644)


class HostsPlanningTests(unittest.TestCase):
    def test_owned_replacement_preserves_surrounding_crlf_bytes(self) -> None:
        content = (b"# untouched\r\n# BEGIN TINY SWARM WORLD\r\n"
                   b"127.0.0.1 old.local\r\n# END TINY SWARM WORLD\r\n# tail\r\n")
        payload = files.desired_hosts(content, ("new.local",))
        self.assertTrue(payload.startswith(b"# untouched\r\n"))
        self.assertTrue(payload.endswith(b"# tail\r\n"))
        self.assertNotIn(b"old.local", payload)
        self.assertEqual(payload, files.desired_hosts(payload, ("new.local",)))

    def test_ambiguous_markers_conflicting_names_and_invalid_names(self) -> None:
        for content in (b"# BEGIN TINY SWARM WORLD\n", b"# END TINY SWARM WORLD\n",
                        b"x # BEGIN TINY SWARM WORLD\n# END TINY SWARM WORLD\n",
                        b"192.0.2.1 Jenkins.Local # conflict\n",
                        b"# BEGIN TINY SWARM WORLD\n# END TINY SWARM WORLD\n"
                        b"# BEGIN TINY SWARM WORLD\n# END TINY SWARM WORLD\n"):
            with self.subTest(content=content):
                with self.assertRaises(ValueError):
                    files.desired_hosts(content, ("jenkins.local",))
        for names in (("name; injection",), ("x", "x"), (), ("\n",)):
            with self.assertRaises(ValueError):
                files.desired_hosts(b"", names)


class DelegationTests(unittest.IsolatedAsyncioTestCase):
    async def test_helper_uses_isolated_python_no_shell_and_private_stdin(self) -> None:
        process = AsyncMock()
        process.returncode = 0
        process.communicate.return_value = (b"", b"")
        before = files.FileObservation(False, b"", "fingerprint", 0, 0, 0)
        with patch.object(async_runner.asyncio, "create_subprocess_exec", return_value=process) as spawn:
            await files.install(Path("/etc/sysctl.d/90-tiny-swarm-world.conf"), before, b"value", 0o644,
                                source_digest=files.helper_source_digest())
        self.assertEqual(("/usr/bin/sudo", "-n", "--", "/usr/bin/python3", "-I", "-B", "-c"),
                         spawn.call_args.args[:7])
        self.assertNotIn("shell", spawn.call_args.kwargs)
        request = json.loads(process.communicate.call_args.args[0])
        self.assertEqual("dmFsdWU=", request["payload"])
        self.assertNotIn("value", str(spawn.call_args))

    async def test_nonzero_exit_does_not_expose_file_content(self) -> None:
        process = AsyncMock()
        process.returncode = 1
        process.communicate.return_value = (b"secret", b"secret")
        with patch.object(async_runner.asyncio, "create_subprocess_exec", return_value=process), \
                patch.object(async_runner.os, "killpg") as killpg:
            with self.assertRaisesRegex(RuntimeError, "fresh plan"):
                await files.install(Path("/etc/hosts"),
                                    files.FileObservation(True, b"secret", "f", 0o644, 0, 0),
                                    b"secret", 0o644, True, source_digest=files.helper_source_digest())
            killpg.assert_not_called()

    async def test_timeout_kills_and_reaps_helper(self) -> None:
        process = AsyncMock()
        process.pid = 43210987
        process.returncode = None
        process.communicate.side_effect = asyncio.TimeoutError
        with patch.object(async_runner.asyncio, "create_subprocess_exec", return_value=process), \
                patch.object(async_runner.os, "killpg") as killpg:
            with self.assertRaises(asyncio.TimeoutError):
                await files.install(Path("/etc/hosts"),
                                    files.FileObservation(True, b"", "f", 0o644, 0, 0), b"", 0o644, True,
                                    source_digest=files.helper_source_digest())
        self.assertEqual([(43210987, signal.SIGTERM), (43210987, signal.SIGKILL)],
                         [call.args for call in killpg.call_args_list])
        self.assertEqual(2, process.wait.await_count)

    async def test_changed_helper_source_blocks_before_privilege(self) -> None:
        digest = files.helper_source_digest()
        with patch.object(files.Path, "read_bytes", return_value=b"raise RuntimeError('tampered')"):
            with patch.object(async_runner.asyncio, "create_subprocess_exec") as spawn:
                with self.assertRaisesRegex(RuntimeError, "source changed"):
                    await files.install(Path("/etc/hosts"),
                                        files.FileObservation(True, b"", "f", 0o644, 0, 0),
                                        b"", 0o644, True, source_digest=digest)
                spawn.assert_not_called()

    async def test_actual_task_cancellation_terminates_reaps_and_propagates(self) -> None:
        process = AsyncMock()
        process.pid = 43210987
        process.returncode = None
        started = asyncio.Event()

        async def communicate(request):
            started.set()
            await asyncio.Future()

        process.communicate.side_effect = communicate
        with patch.object(async_runner.asyncio, "create_subprocess_exec", return_value=process), \
                patch.object(async_runner.os, "killpg") as killpg:
            task = asyncio.create_task(files.install(
                Path("/etc/hosts"), files.FileObservation(True, b"", "f", 0o644, 0, 0),
                b"", 0o644, True, source_digest=files.helper_source_digest()))
            await asyncio.wait_for(started.wait(), timeout=1)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        self.assertEqual([(43210987, signal.SIGTERM), (43210987, signal.SIGKILL)],
                         [call.args for call in killpg.call_args_list])
        self.assertEqual(2, process.wait.await_count)

    async def test_unresponsive_termination_escalates_kill_and_reaps(self) -> None:
        process = AsyncMock()
        process.returncode = None
        process.pid = 43210987
        process.communicate.side_effect = asyncio.TimeoutError
        process.wait.side_effect = [asyncio.TimeoutError, 0]
        with patch.object(async_runner.asyncio, "create_subprocess_exec", return_value=process), \
                patch.object(async_runner.os, "killpg") as killpg:
            with self.assertRaises(asyncio.TimeoutError):
                await files.install(Path("/etc/hosts"),
                                    files.FileObservation(True, b"", "f", 0o644, 0, 0),
                                    b"", 0o644, True, source_digest=files.helper_source_digest())
        self.assertEqual([(43210987, signal.SIGTERM), (43210987, signal.SIGKILL)],
                         [call.args for call in killpg.call_args_list])
        self.assertEqual(2, process.wait.await_count)

    async def test_launch_failure_becomes_generic_safe_error(self) -> None:
        with patch.object(async_runner.asyncio, "create_subprocess_exec",
                          side_effect=FileNotFoundError("private launch detail")):
            with self.assertRaisesRegex(RuntimeError, "fresh plan") as raised:
                await files.install(Path("/etc/hosts"),
                                    files.FileObservation(True, b"private hosts", "f", 0o644, 0, 0),
                                    b"private hosts", 0o644, True,
                                    source_digest=files.helper_source_digest())
        self.assertNotIn("private", str(raised.exception))
        self.assertIsNone(raised.exception.__cause__)
