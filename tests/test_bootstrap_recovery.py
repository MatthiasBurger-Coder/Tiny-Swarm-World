"""BOOT-W08 acceptance: durable state, observed resume and private evidence."""
from __future__ import annotations

import asyncio
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from tiny_swarm_world.application.ports.native_preparation import HostPackagePreparationFailure
from tiny_swarm_world.infrastructure.adapters.native_package_manager import AptHostPackageManager
from tiny_swarm_world.application.services.incus_preparation import IncusPreparationService
from tiny_swarm_world.domain.incus_preparation import IncusAction, IncusSnapshot
from tiny_swarm_world.infrastructure.adapters.bootstrap_state import BootstrapState
from tiny_swarm_world.infrastructure.adapters.native_preparation_evidence import NativePreparationEvidenceWriter

IDENTITY = {"contract": "bootstrap-v1", "host_sha256": "a" * 64, "release": "24.04", "selection": "service-access"}
CONTEXT = "tiny_swarm_world.infrastructure.adapters.native_preparation_evidence.context"


class ProtectedCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.identity = patch(CONTEXT, return_value=IDENTITY)
        self.identity.start()
        self.addCleanup(self.identity.stop)
        self.writer = NativePreparationEvidenceWriter(self.root)
        self.addCleanup(self.writer._checkpoint.close)

    def write(self, status="pending", **kwargs):
        return self.writer.write(platform_release="24.04", status=status, planned=("incus",),
                                 added=(), uncertain=("incus",), stage="apt_install", **kwargs)

    @property
    def state(self):
        return self.root / "tiny-swarm-world/bootstrap/packages.state.json"

    def test_ac2_read_only_validation_creates_nothing(self):
        self.writer.validate(platform_release="24.04")
        self.assertEqual(list(self.root.iterdir()), [])

    def test_ac3_durable_stage_version_exit_context_and_no_raw_output(self):
        evidence = self.write("interrupted", exit_code=130)
        payload = json.loads(evidence.read_text())
        state = json.loads(self.state.read_text())
        self.assertEqual(state["record"]["stage"], "apt_install")
        self.assertEqual(state["record"]["exit_code"], 130)
        self.assertEqual(payload["context"], IDENTITY)
        self.assertEqual(payload["operation"], state["operation"])
        for path in (evidence, self.state):
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertNotIn("stdout", path.read_text())
        self.assertEqual(self.state.parent.stat().st_mode & 0o777, 0o700)

    def test_ac2_corrupt_stale_and_foreign_state_are_preserved_and_block_write(self):
        self.write("failed")
        valid = self.state.read_text()
        vectors = ["{", '{"schema":1,"schema":1}', valid.replace('"release": "24.04"', '"release": "26.04"'),
                   valid.replace('"schema": 1', '"schema": true'),
                   valid.replace('"exit_code": 1', '"exit_code": "1"'),
                   valid.replace('"status": "failed"', '"status": "trusted"')]
        for value in vectors:
            with self.subTest(value=value[:40]):
                self.state.write_text(value)
                before = {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
                with self.assertRaises(OSError):
                    NativePreparationEvidenceWriter(self.root).validate(platform_release="24.04")
                with self.assertRaises(OSError):
                    self.write("started")
                self.assertEqual(before, {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()})

    def test_ac2_symlink_hardlink_modes_and_ancestor_collisions_block(self):
        self.write("failed")
        original = self.state.read_bytes()
        self.state.chmod(0o644)
        with self.assertRaises(OSError):
            self.writer.validate(platform_release="24.04")
        self.state.chmod(0o600)
        other = self.root / "foreign"
        os.link(self.state, other)
        with self.assertRaises(OSError):
            self.writer.validate(platform_release="24.04")
        other.unlink()
        self.state.unlink()
        other.write_bytes(original)
        self.state.symlink_to(other)
        with self.assertRaises(OSError):
            self.writer.validate(platform_release="24.04")
        self.assertEqual(other.read_bytes(), original)
        linked = self.root / "linked"
        linked.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(OSError):
            BootstrapState(linked / "tiny-swarm-world/bootstrap").validate("packages", IDENTITY)

    def test_ac1_concurrent_apply_cannot_pass_pending_intent(self):
        self.write()
        second = NativePreparationEvidenceWriter(self.root)
        with self.assertRaises(BlockingIOError):
            second.write(platform_release="24.04", status="started", planned=("incus",), added=(),
                         uncertain=("incus",), stage="apt_install")
        self.write("failed")
        second.write(platform_release="24.04", status="succeeded", planned=("incus",), added=("incus",),
                     uncertain=(), stage="apt_verify")

    def test_ac1_interrupted_atomic_publication_preserves_previous_checkpoint(self):
        self.write("failed")
        before = self.state.read_bytes()
        with patch("tiny_swarm_world.infrastructure.adapters.bootstrap_state.os.replace", side_effect=OSError("publish_failed")):
            with self.assertRaises(OSError):
                self.write("started")
        self.assertEqual(self.state.read_bytes(), before)
        self.assertFalse(list(self.state.parent.glob(".checkpoint-*")))

    def test_ac3_secret_labels_rejected_before_creating_storage(self):
        with self.assertRaises(OSError):
            self.writer.write(platform_release="24.04", status="failed", planned=("password:abc",),
                              added=(), uncertain=(), stage="apt_install")
        self.assertEqual(list(self.root.iterdir()), [])

    def test_ac2_selection_is_part_of_context(self):
        from tiny_swarm_world.infrastructure.adapters.bootstrap_state import context
        # Do not mock this identity comparison: the real producer binds selection.
        self.assertNotEqual(context("24.04", "default"), context("24.04", "service-access"))


class PackageExitContextTests(unittest.TestCase):
    def test_ac3_failed_apt_stage_preserves_exit_and_redacts_native_output(self):
        for code, expected in ((100, 100), (-15, 143)):
            runner = Mock()
            runner.run_text.return_value = Mock(returncode=code, stdout="private-key-secret", stderr="password-value")
            with self.assertRaises(HostPackagePreparationFailure) as caught:
                AptHostPackageManager(runner).install(("incus",))
            self.assertEqual(caught.exception.stage, "apt_index_refresh")
            self.assertEqual(caught.exception.exit_code, expected)
            self.assertNotIn("private-key-secret", str(caught.exception))
            self.assertNotIn("password-value", str(caught.exception))
            self.assertEqual(runner.run_text.call_count, 1)


class ObservedResumeTests(unittest.IsolatedAsyncioTestCase):
    async def test_ac1_interrupted_incus_resume_skips_observed_completed_mutation(self):
        with tempfile.TemporaryDirectory() as directory, patch(CONTEXT, return_value=IDENTITY):
            root = Path(directory)
            actions = [IncusAction("create:storage-pools:pool", "storage-pools", "pool"),
                       IncusAction("create:networks:bridge", "networks", "bridge")]
            remaining = list(actions)
            calls = []
            class Port:
                def __init__(self, interrupt):
                    self.writer = NativePreparationEvidenceWriter(root)
                    self.interrupt = interrupt
                async def inspect(self):
                    fingerprint = hashlib.sha256(repr(remaining).encode()).hexdigest()
                    snapshot = IncusSnapshot(fingerprint, tuple(remaining), verified=not remaining)
                    try:
                        self.writer.validate(platform_release="24.04", capability="incus")
                    except OSError:
                        snapshot = replace(snapshot, blockers=("invalid_state",))
                    return snapshot
                async def execute(self, action):
                    calls.append(action.id)
                    if self.interrupt and action == actions[1]:
                        raise asyncio.CancelledError
                    remaining.remove(action)
                async def action_verified(self, action):
                    return action not in remaining
                def record(self, status, planned, completed, uncertain, *, exit_code=None):
                    return str(self.writer.write(platform_release="24.04", status=status, planned=planned,
                               added=completed, uncertain=uncertain, stage=uncertain[-1] if uncertain else "incus_preparation",
                               capability="incus", exit_code=exit_code))
            first = Port(True)
            service = IncusPreparationService(first)
            with self.assertRaises(asyncio.CancelledError):
                await service.apply(await service.plan(), approved=True)
            state = json.loads((root / "tiny-swarm-world/bootstrap/incus.state.json").read_text())
            self.assertEqual(state["record"]["confirmed"], [actions[0].id])
            self.assertEqual(state["record"]["exit_code"], 130)
            resumed = IncusPreparationService(Port(False))
            plan = await resumed.plan()
            result = await resumed.apply(plan, approved=False)
            self.assertEqual(result.status, "BLOCKED")
            result = await resumed.apply(plan, approved=True)
            self.assertEqual(result.status, "READY")
            self.assertEqual(calls.count(actions[0].id), 1)
            self.assertEqual(calls.count(actions[1].id), 2)
            # Saved READY is never readiness: changed observation proposes work again.
            remaining.append(actions[0])
            self.assertEqual((await resumed.plan()).actions, (actions[0],))


class InterpreterCheckpointTests(unittest.TestCase):
    def test_ac2_ac3_shell_state_validation_is_write_free_and_retains_actual_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = Path("tools/ubuntu_python_prerequisites.sh").resolve()
            script = '''source "$1"
                umask 077
                mkdir -p "$2/tiny-swarm-world/evidence/native-preparation"
                checkpoint="$2/tiny-swarm-world/evidence/native-preparation/interpreter.state"
                identity=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
                tsw_interpreter_checkpoint "$checkpoint" "$identity" interpreter-abcdef apt_install_pending failed 124 'python3 python3-venv' python3 python3-venv
                tsw_interpreter_validate "$checkpoint" "$identity" || exit 11
                before=$(sha256sum "$checkpoint")
                tsw_interpreter_validate "$checkpoint" "$identity" || exit 12
                [[ "$(sha256sum "$checkpoint")" == "$before" ]] || exit 13
                tsw_interpreter_validate "$checkpoint" foreign && exit 14
                grep -q '^exit_code=124$' "$checkpoint" || exit 15
                grep -q '^confirmed=python3$' "$checkpoint" || exit 16
                operation=interpreter-abcdef
                tsw_transport_exit=124
                evidence="$2/tiny-swarm-world/evidence/native-preparation/run"
                : > "$evidence"
                timeout() { [[ "${@: -1}" == python3 ]] && printf 'install ok installed' || return 1; }
                tsw_interpreter_partial "$evidence" python3 python3-venv
                grep -q '^confirmed=python3$' "$checkpoint" || exit 17
                grep -q '^uncertain=python3-venv$' "$checkpoint" || exit 18
                grep -q '^exit_code=124$' "$checkpoint" || exit 19
                printf PASS
            '''
            result = subprocess.run(["bash", "-c", script, "test", str(source), str(root)], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout, "PASS")
            self.assertIn("stopped at stage apt_install_pending", result.stderr)
            valid = (root / "tiny-swarm-world/evidence/native-preparation/interpreter.state").read_text()
            checkpoint = root / "tiny-swarm-world/evidence/native-preparation/interpreter.state"
            for field, replacement in (
                ("exit_code=124", "exit_code=999999"),
                ("timestamp_utc=", "timestamp_utc=999999999999999"),
                ("uncertain=python3-venv", "uncertain=python3"),
                ("planned=python3 python3-venv", "planned=python3-venv"),
                ("exit_code=124", "exit_code=124=extra"),
            ):
                with self.subTest(field=field, replacement=replacement):
                    corrupt = valid.replace(field, replacement)
                    checkpoint.write_text(corrupt)
                    checked = subprocess.run(["bash", "-c", 'source "$1"; tsw_interpreter_validate "$2" "$3"', "test", str(source), str(checkpoint), "a" * 64], capture_output=True, text=True, timeout=10)
                    self.assertNotEqual(checked.returncode, 0)
                    self.assertEqual(checkpoint.read_text(), corrupt)
