"""Selection admission and persistence using synthetic inventory and checkout identity."""

import hashlib
import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch
from uuid import UUID

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.lifecycle import InstallationLifecycleService
from tiny_swarm_world.application.services.service_selection import ServiceSelectionService
from tiny_swarm_world.domain.lifecycle.models import ConfigurationReference, CredentialReference
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.adapters.lifecycle.setup_state import SetupSelectionState
from tiny_swarm_world.infrastructure.process.runner import ProcessRunner, ProcessTimeoutError


ROOT = Path(__file__).resolve().parents[4]


class SetupSelectionStateTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.checkout = self.root / "prepared"
        self.checkout.mkdir()
        (self.checkout / "pyproject.toml").write_text('[project]\nversion = "0.2.0"\n')
        (self.checkout / "requirements.lock").write_bytes(b"synthetic-lock-fixture\n")
        self.path = self.root / "private" / "manifest.json"
        self.repository = JsonManifestRepository(self.path)
        self.catalog = NativeComponentCatalog(ROOT)
        self.lifecycle = InstallationLifecycleService(self.repository, self.catalog)
        self.selection = ServiceSelectionService(self.repository, self.catalog)
        self.nodes = ("swarm-manager", "swarm-worker-1")

    def _runner(self, inventory="[]", returncode=0):
        runner = Mock(spec=ProcessRunner)
        runner.run_text.side_effect = [
            subprocess.CompletedProcess(("incus", "list"), returncode, stdout=inventory),
            subprocess.CompletedProcess(("git", "rev-parse"), 0, stdout="a" * 40 + "\n"),
        ]
        return runner

    def _state(self, plan=None):
        return SetupSelectionState(
            self.lifecycle, plan or self.selection.preview(minimal=True), self.checkout,
        )

    def _admit(self, state, runner):
        state.admit(runner, backend="incus", node_names=self.nodes, host="native-linux")

    def _adopt_minimal_with_observations(self):
        state = self._state()
        self._admit(state, self._runner())
        manifest = state.fresh
        self.assertIsNotNone(manifest)
        manifest = manifest.model_copy(update={
            "components": tuple(item.model_copy(update={"observed": item.desired})
                                for item in manifest.components),
            "credential_references": (
                CredentialReference(key="TSW_PORTAINER_ADMIN_PASSWORD", source="external_user_secret"),
            ),
            "configuration_references": (
                ConfigurationReference(key="site", source="operator_override", reference="site-config"),
            ),
            "operation_reference": "previous-operation",
            "checkpoint_reference": "previous-checkpoint",
        })
        self.repository.save(manifest, expected_token=None)
        return manifest

    def test_empty_inventory_admission_creates_no_state_until_commit(self):
        state = self._state()
        runner = self._runner()

        self._admit(state, runner)

        self.assertFalse(self.path.parent.exists())
        self.assertEqual(runner.run_text.call_count, 2)
        self.assertEqual(
            runner.run_text.call_args_list[0].args,
            (("incus", "list", "--format", "json"),),
        )
        self.assertEqual(runner.run_text.call_args_list[0].kwargs, {"timeout": 10})
        self.assertEqual(runner.run_text.call_args_list[1].kwargs,
                         {"cwd": self.checkout, "timeout": 5})
        state.commit()
        self.assertEqual(self.repository.load().manifest, state.fresh)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)

    def test_fresh_identity_records_desired_versions_without_runtime_observations(self):
        state = self._state()
        self._admit(state, self._runner())
        manifest = state.fresh

        self.assertEqual(str(UUID(manifest.installation_id)), manifest.installation_id)
        self.assertEqual(manifest.host, "native-linux")
        self.assertEqual(manifest.runtime_profile, "classic")
        self.assertEqual(manifest.product.release, "0.2.0")
        self.assertEqual(manifest.product.revision, "a" * 40)
        self.assertEqual(manifest.product.dependency_lock,
                         "sha256:" + hashlib.sha256(b"synthetic-lock-fixture\n").hexdigest())
        self.assertEqual(manifest.requested_services, ())
        self.assertEqual(manifest.resolved_services, ("incus", "portainer"))
        expected = tuple(item for service in self.catalog.load().services
                         if service.service_id in manifest.resolved_services for item in service.components)
        self.assertEqual(manifest.components, expected)
        self.assertTrue(all(item.observed is None for item in manifest.components))
        self.catalog.load().validate_manifest(manifest)
        self.assertFalse(self.path.parent.exists())

    def test_existing_node_or_ownership_marker_refuses_before_writes(self):
        inventories = (
            [{"name": "swarm-manager", "config": {}}],
            [{"name": "another-node", "config": {"user.tiny_swarm_world.installation": "synthetic"}}],
        )
        for inventory in inventories:
            with self.subTest(inventory=inventory):
                state = self._state()
                runner = self._runner(json.dumps(inventory))
                with self.assertRaisesRegex(LifecycleStateError, "adopt"):
                    self._admit(state, runner)
                runner.run_text.assert_called_once()
                self.assertIsNone(state.fresh)
                self.assertFalse(self.path.parent.exists())

    def test_malformed_or_failed_inventory_refuses_before_identity_or_writes(self):
        cases = (("not-json", 0), ("{}", 0), ('[{"name":"x"}]', 0),
                 ('[{"name":7,"config":{}}]', 0), ("[null]", 0), ("[]", 1))
        for payload, returncode in cases:
            with self.subTest(payload=payload, returncode=returncode):
                state = self._state()
                runner = self._runner(payload, returncode)
                with self.assertRaisesRegex(LifecycleStateError, "Cannot prove"):
                    self._admit(state, runner)
                runner.run_text.assert_called_once()
                self.assertFalse(self.path.parent.exists())
        runner = self._runner()
        runner.run_text.side_effect = ProcessTimeoutError()
        with self.assertRaisesRegex(LifecycleStateError, "Cannot prove"):
            self._admit(self._state(), runner)
        self.assertFalse(self.path.parent.exists())

    def test_stale_admission_refuses_without_inventory_or_write(self):
        plan = self.selection.preview(minimal=True)
        self._adopt_minimal_with_observations()
        before = self.path.read_bytes()
        runner = self._runner()

        with self.assertRaisesRegex(LifecycleStateError, "stale"):
            self._admit(self._state(plan), runner)

        runner.run_text.assert_not_called()
        self.assertEqual(self.path.read_bytes(), before)

    def test_existing_addition_preserves_identity_provenance_and_observations(self):
        original = self._adopt_minimal_with_observations()
        plan = self.selection.preview(("jenkins",), add=True)
        state = self._state(plan)
        runner = self._runner()
        before = self.path.read_bytes()
        self._admit(state, runner)
        runner.run_text.assert_not_called()
        self.assertEqual(self.path.read_bytes(), before)

        state.commit()

        saved = self.repository.load().manifest
        for field in ("installation_id", "product", "configuration_references",
                      "operation_reference", "checkpoint_reference"):
            with self.subTest(field=field):
                self.assertEqual(getattr(saved, field), getattr(original, field))
        for reference in original.credential_references:
            self.assertIn(reference, saved.credential_references)
        self.assertEqual(saved.resolved_services, ("incus", "portainer", "nexus", "jenkins"))
        self.assertEqual(saved.selection_reasons["nexus"], ("jenkins",))
        for component in original.components:
            self.assertIn(component, saved.components)
        self.assertTrue(all(item.observed is None for item in saved.components
                            if item.service_id in {"nexus", "jenkins"}))
        stamp = self.path.stat().st_mtime_ns
        content = self.path.read_bytes()
        repeated = self._state(self.selection.preview())
        self._admit(repeated, runner)
        repeated.commit()
        self.assertEqual(self.path.read_bytes(), content)
        self.assertEqual(self.path.stat().st_mtime_ns, stamp)
        runner.run_text.assert_not_called()

    def test_commit_after_concurrent_selection_change_preserves_newer_state(self):
        self._adopt_minimal_with_observations()
        state = self._state(self.selection.preview(("jenkins",), add=True))
        self._admit(state, self._runner())
        self.selection.persist(self.selection.preview(("swagger",), add=True), approved=True)
        before = self.path.read_bytes()

        with self.assertRaisesRegex(LifecycleStateError, "stale"):
            state.commit()

        self.assertEqual(self.path.read_bytes(), before)

    def test_commit_compare_and_swap_rejects_race_during_save(self):
        self._adopt_minimal_with_observations()
        state = self._state(self.selection.preview(("jenkins",), add=True))
        self._admit(state, self._runner())
        real_save = self.repository.save
        concurrent = self.repository.load().manifest.model_copy(update={"checkpoint_reference": "concurrent"})

        def concurrent_save(manifest, *, expected_token):
            real_save(concurrent, expected_token=expected_token)
            return real_save(manifest, expected_token=expected_token)

        with patch.object(self.repository, "save", side_effect=concurrent_save):
            with self.assertRaisesRegex(LifecycleStateError, "state changed"):
                state.commit()

        self.assertEqual(self.repository.load().manifest, concurrent)

    def test_failed_commit_preserves_manifest_and_does_not_report_success(self):
        self._adopt_minimal_with_observations()
        state = self._state(self.selection.preview(("jenkins",), add=True))
        self._admit(state, self._runner())
        before = self.path.read_bytes()

        with patch("tiny_swarm_world.infrastructure.adapters.lifecycle.manifest.os.replace",
                   side_effect=OSError("synthetic-write-failure")):
            with self.assertRaisesRegex(LifecycleStateError, "interrupted"):
                state.commit()

        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse(tuple(self.path.parent.glob("*.tmp")))

    def test_copied_manifest_host_is_refused_before_runtime(self):
        self._adopt_minimal_with_observations()
        state = self._state(self.selection.preview())
        runner = self._runner()
        with self.assertRaisesRegex(LifecycleStateError, "host differs"):
            state.admit(runner, backend="incus", node_names=self.nodes, host="wsl2")
        runner.run_text.assert_not_called()

    def test_selected_override_inventory_and_symbolic_provenance_are_persisted(self):
        plan = self.selection.preview(("jenkins",))
        state = self._state(plan)
        with patch.dict("os.environ", {"TSW_JENKINS_IMAGE": "127.0.0.1:13500/jenkins:0.2.1"}):
            self._admit(state, self._runner())
            state.commit()
        saved = self.repository.load().manifest
        jenkins = next(item for item in saved.components if item.component_id == "jenkins")
        self.assertEqual(jenkins.desired.image_tag, "0.2.1")
        self.assertIsNone(jenkins.observed)
        self.assertIn("tsw_jenkins_image", {item.key for item in saved.configuration_references})
        self.assertIn("TSW_JENKINS_ADMIN_PASSWORD", {item.key for item in saved.credential_references})
        self.assertNotIn("0.2.1", str(saved.configuration_references))
