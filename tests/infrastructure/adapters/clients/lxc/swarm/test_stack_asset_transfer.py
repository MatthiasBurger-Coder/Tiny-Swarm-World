from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from unittest.mock import Mock

from tiny_swarm_world.infrastructure.adapters.clients.lxc.swarm.stack_asset_transfer import (
    StackAssetTransfer,
)
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths


class TestStackAssetTransfer(unittest.TestCase):
    def test_registry_dispatches_to_matching_strategy_and_stops(self):
        first = Mock()
        first.supports.return_value = False
        second = Mock()
        second.supports.return_value = True
        transfer = StackAssetTransfer(
            project_paths=ProjectPaths.from_roots(Path("/tmp/project")),
            run_manager_shell=Mock(),
            render_service_access_dashboard=Mock(),
            strategies=(first, second),
        )

        transfer.transfer_stack_assets("custom", "/remote/custom")

        first.supports.assert_called_once_with("custom")
        second.supports.assert_called_once_with("custom")
        second.transfer.assert_called_once()

    def test_service_access_asset_uses_generated_dashboard(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            transfer = StackAssetTransfer(
                project_paths=ProjectPaths.from_roots(Path(temporary_directory)),
                run_manager_shell=Mock(),
                render_service_access_dashboard=lambda: "<html>generated</html>",
            )

            transfer.transfer_stack_assets("service-access", "/remote/service-access")

        transfer._run_manager_shell.assert_called_once()
        call = transfer._run_manager_shell.call_args
        self.assertIn("target=/remote/service-access/dashboard/index.html", call.args[0])
        self.assertEqual(call.kwargs["input_text"], "<html>generated</html>")
        self.assertTrue(call.kwargs["retry_safe"])

    def test_unknown_stack_has_no_asset_side_effect(self):
        run_manager_shell = Mock()
        transfer = StackAssetTransfer(
            project_paths=ProjectPaths.from_roots(Path("/tmp/project")),
            run_manager_shell=run_manager_shell,
            render_service_access_dashboard=Mock(),
        )

        transfer.transfer_stack_assets("unknown", "/remote/unknown")

        run_manager_shell.assert_not_called()


class TestAssetTransferFilesystem(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.destination = self.root / "remote 'quoted'" / "dashboard" / "index.html"
        self.received: str | None = None
        self.environment = dict(os.environ)
        self.transfer = StackAssetTransfer(
            project_paths=ProjectPaths.from_roots(self.root),
            run_manager_shell=self.run_shell,
            render_service_access_dashboard=lambda: "first\n",
        )

    def run_shell(self, script, *, input_text, **kwargs):
        payload = input_text if self.received is None else self.received
        return subprocess.run(
            ["sh", "-c", script], input=payload, text=True,
            capture_output=True, check=True, timeout=5, env=self.environment, cwd=self.root,
        )

    def transfer_dashboard(self):
        self.transfer.transfer_stack_assets("service-access", str(self.destination.parent.parent))

    def test_identical_transfer_preserves_inode_mode_and_mtime(self):
        self.transfer_dashboard()
        self.destination.chmod(0o640)
        os.utime(self.destination, ns=(1_000_000_000, 1_000_000_000))
        before = self.destination.stat()
        self.transfer_dashboard()
        after = self.destination.stat()
        self.assertEqual(self.destination.read_bytes(), b"first\n")
        self.assertEqual((after.st_ino, after.st_mode, after.st_mtime_ns),
                         (before.st_ino, before.st_mode, before.st_mtime_ns))

    def test_truncated_receive_preserves_existing_asset(self):
        self.transfer_dashboard()
        before = self.destination.stat()
        self.received = "fir"
        with self.assertRaises(subprocess.CalledProcessError):
            self.transfer_dashboard()
        self.assertEqual(self.destination.read_bytes(), b"first\n")
        self.assertEqual(self.destination.stat().st_mtime_ns, before.st_mtime_ns)
        self.assertEqual(list(self.destination.parent.iterdir()), [self.destination])

    def test_failed_initial_receive_does_not_publish_asset(self):
        self.received = ""
        with self.assertRaises(subprocess.CalledProcessError):
            self.transfer_dashboard()
        self.assertFalse(self.destination.exists())

    def test_changed_payload_preserves_inode_and_literal_content(self):
        self.transfer_dashboard()
        inode = self.destination.stat().st_ino
        for content in ("$(touch forbidden) `false` ' \" ;\n\n", "", "last\n"):
            with self.subTest(content=content):
                self.transfer._render_service_access_dashboard = lambda: content
                self.transfer_dashboard()
                self.assertEqual(self.destination.read_text(), content)
                self.assertEqual(self.destination.stat().st_ino, inode)
                self.assertFalse((self.root / "forbidden").exists())

    def test_symlink_target_is_rejected_without_changing_referent(self):
        self.destination.parent.mkdir(parents=True)
        other = self.root / "foreign"
        other.write_text("preserve")
        self.destination.symlink_to(other)
        with self.assertRaises(subprocess.CalledProcessError):
            self.transfer_dashboard()
        self.assertEqual(other.read_text(), "preserve")

    def test_same_length_corruption_is_rejected(self):
        self.transfer_dashboard()
        self.received = "wrong\n"
        with self.assertRaises(subprocess.CalledProcessError):
            self.transfer_dashboard()
        self.assertEqual(self.destination.read_bytes(), b"first\n")

    def test_changed_content_is_visible_through_existing_open_descriptor(self):
        self.transfer_dashboard()
        self.destination.chmod(0o640)
        with self.destination.open("rb") as mounted:
            self.transfer._render_service_access_dashboard = lambda: "changed\n"
            self.transfer_dashboard()
            self.assertEqual(mounted.read(), b"changed\n")
        self.assertEqual(self.destination.stat().st_mode & 0o777, 0o640)
        self.assertEqual(list(self.destination.parent.iterdir()), [self.destination])

    def test_repairs_previously_truncated_asset(self):
        self.destination.parent.mkdir(parents=True)
        self.destination.touch()
        inode = self.destination.stat().st_ino
        self.transfer_dashboard()
        self.assertEqual(self.destination.read_bytes(), b"first\n")
        self.assertEqual(self.destination.stat().st_ino, inode)

    def test_receive_command_failure_preserves_destination_and_cleans_stage(self):
        self.transfer_dashboard()
        self.install_failing_cat('if [ "$#" -eq 0 ]; then printf partial; exit 9; fi')
        with self.assertRaises(subprocess.CalledProcessError) as caught:
            self.transfer_dashboard()
        self.assertEqual(caught.exception.returncode, 9)
        self.assertEqual(self.destination.read_bytes(), b"first\n")
        self.assertEqual(list(self.destination.parent.iterdir()), [self.destination])

    def test_local_publication_failure_is_not_success(self):
        self.transfer_dashboard()
        self.install_failing_cat('if [ "$#" -ne 0 ]; then exit 7; fi')
        self.transfer._render_service_access_dashboard = lambda: "changed\n"
        with self.assertRaises(subprocess.CalledProcessError) as caught:
            self.transfer_dashboard()
        self.assertEqual(caught.exception.returncode, 7)
        self.assertEqual(list(self.destination.parent.iterdir()), [self.destination])

    def install_failing_cat(self, condition):
        tools = self.root / "tools"
        tools.mkdir()
        executable = tools / "cat"
        executable.write_text('#!/bin/sh\n' + condition + '\nexec /bin/cat "$@"\n')
        executable.chmod(0o700)
        self.environment["PATH"] = str(tools) + os.pathsep + self.environment["PATH"]
