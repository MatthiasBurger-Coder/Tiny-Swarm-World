"""Selection admission and persistence using synthetic inventory and checkout identity."""

import asyncio
from dataclasses import replace
import hashlib
import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.ports.update import PortUpdateRuntimeObserver, UpdateObservationChanged
from tiny_swarm_world.application.services.lifecycle import InstallationLifecycleService
from tiny_swarm_world.application.services.service_selection import ServiceSelectionService
from tiny_swarm_world.domain.lifecycle.models import ConfigurationReference, CredentialReference
from tiny_swarm_world.domain.lifecycle.update_planning import plan_component_updates
from tiny_swarm_world.domain.update import UpdateRuntimeObservation, UpdateTaskObservation
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tiny_swarm_world.infrastructure.adapters.lifecycle.setup_state import SetupSelectionState
from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import IMAGE_OVERRIDE_ENVIRONMENT_BY_CONTEXT
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


class SetupSourceObservationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "pyproject.toml").write_text('[project]\nversion = "0.2.0"\n')
        (self.root / "requirements.lock").write_text("synthetic-lock\n")
        self.repository = JsonManifestRepository(self.root / ".tiny-swarm-world/installation/manifest.json")
        self.catalog = NativeComponentCatalog(ROOT)
        self.lifecycle = InstallationLifecycleService(self.repository, self.catalog)
        self.selection = ServiceSelectionService(self.repository, self.catalog)

    def _pins(self, services, *, target=False):
        environment = {}
        for service in self.catalog.load().services:
            if service.service_id not in services:
                continue
            transition = service.update_transitions[0]
            versions = (next(t.versions for t in service.update_targets if t.target_id == transition.target_id)
                        if target else transition.source_versions)
            for name, version in versions.items():
                environment[IMAGE_OVERRIDE_ENVIRONMENT_BY_CONTEXT[name]] = version.image_repository + "@" + version.image_digest
        return environment

    def _prepare(self, services=("swagger",), *, environment=None, add=False):
        plan = self.selection.preview(services or None, minimal=not services, add=add)
        state = SetupSelectionState(self.lifecycle, plan, self.root)
        runner = Mock(spec=ProcessRunner)
        runner.run_text.side_effect = [subprocess.CompletedProcess([], 0, stdout="[]"),
                                       subprocess.CompletedProcess([], 0, stdout="a" * 40)]
        with patch.dict("os.environ", environment or {}, clear=True):
            state.admit(runner, backend="incus", node_names=("swarm-manager",), host="native-linux")
        return state

    def _observer(self, state, *, fault=None):
        components = {item.component_id: item for item in state.component_inventory}

        async def observe(stack, name):
            desired = components[name].desired
            reference = desired.image_repository + ":recorded-tag@" + desired.image_digest
            result = UpdateRuntimeObservation(stack, name, "service-" + name, 1, reference, 1,
                (UpdateTaskObservation("task-" + name, reference, "running", "running"),), "completed")
            return fault(result) if fault is not None else result

        return Mock(spec=PortUpdateRuntimeObserver, observe=AsyncMock(side_effect=observe))

    async def test_complete_fresh_observations_enrich_both_payloads_and_admit_real_update(self):
        state = self._prepare(("swagger", "traefik"), environment=self._pins(("swagger", "traefik")))
        original = state.fresh
        self.assertTrue(state.observation_required)
        with self.assertRaisesRegex(LifecycleStateError, "observations"):
            state.commit()
        self.assertIsNone(self.repository.load().manifest)
        observer = self._observer(state)
        await state.observe_new_components(observer)
        self.assertEqual(observer.observe.await_count, 5)
        self.assertEqual(state.fresh.components, state.component_inventory)
        for item in state.component_inventory:
            if item.service_id in {"swagger", "traefik"}:
                self.assertEqual(item.observed.image_tag, "recorded-tag")
                self.assertIsNone(item.desired.image_tag)
                self.assertIsNone(item.observed.upstream_version)
                self.assertIsNone(item.observed.build_identity)
                self.assertEqual(item.desired.image_digest, item.observed.image_digest)
            else:
                self.assertIn(item, original.components)
        state.commit()
        saved = self.repository.load().manifest
        self.assertEqual(saved, state.fresh)
        self.assertEqual(saved.installation_id, original.installation_id)
        self.assertEqual(saved.credential_references, original.credential_references)
        self.assertEqual(plan_component_updates(self.catalog.load(), saved, ("swagger", "traefik")).status, "blocked")

    async def test_candidate_target_observations_do_not_enable_unqualified_noop(self):
        state = self._prepare(environment=self._pins(("swagger",), target=True))
        await state.observe_new_components(self._observer(state))
        state.commit()
        self.assertEqual(plan_component_updates(self.catalog.load(), self.repository.load().manifest, ("swagger",)).status, "blocked")

    async def test_add_observes_only_new_bundle_and_preserves_every_existing_field(self):
        minimal = self._prepare(())
        minimal.commit()
        original = self.repository.load().manifest
        state = self._prepare(environment=self._pins(("swagger",)), add=True)
        observer = self._observer(state)
        await state.observe_new_components(observer)
        self.assertEqual(observer.observe.await_count, 4)
        state.commit()
        saved = self.repository.load().manifest
        for item in original.components:
            self.assertIn(item, saved.components)
        for field in ("installation_id", "product", "credential_references", "operation_reference", "checkpoint_reference"):
            self.assertEqual(getattr(saved, field), getattr(original, field))
        self.assertTrue(all(reference in saved.configuration_references for reference in original.configuration_references))
        self.assertEqual(plan_component_updates(self.catalog.load(), saved, ("swagger",)).status, "blocked")

    async def test_tag_only_partial_and_unknown_pins_skip_without_fabricating_observations(self):
        pinned = self._pins(("swagger",))
        partial = dict(pinned)
        partial.pop("TSW_SWAGGER_UI_IMAGE")
        unknown = dict(pinned, TSW_SWAGGER_UI_IMAGE="swaggerapi/swagger-ui@sha256:" + "f" * 64)
        for environment in ({}, partial, unknown):
            with self.subTest(environment_keys=tuple(environment)):
                state = self._prepare(environment=environment)
                before = state.component_inventory
                observer = self._observer(state)
                self.assertFalse(state.observation_required)
                await state.observe_new_components(observer)
                observer.observe.assert_not_awaited()
                self.assertEqual(state.component_inventory, before)
                self.assertTrue(all(item.observed is None for item in before))
        minimal = self._prepare(())
        self.assertFalse(minimal.observation_required)

    async def test_existing_unknown_pinned_bundle_is_not_a_general_refresh(self):
        environment = self._pins(("swagger",))
        historical = self._prepare(environment=environment).fresh
        # Simulate a schema-1 manifest produced before the observation hook existed.
        self.repository.save(historical, expected_token=None)
        state = self._prepare(environment=environment)
        before = self.repository.path.read_bytes()
        stamp = self.repository.path.stat().st_mtime_ns
        observer = self._observer(state)
        self.assertFalse(state.observation_required)
        await state.observe_new_components(observer)
        state.commit()
        observer.observe.assert_not_awaited()
        self.assertEqual(self.repository.path.read_bytes(), before)
        self.assertEqual(self.repository.path.stat().st_mtime_ns, stamp)

    async def test_wrong_old_mixed_missing_or_paused_tasks_never_partially_enrich(self):
        wrong = "swaggerapi/swagger-ui@sha256:" + "f" * 64
        faults = (
            lambda r: replace(r, desired_image=wrong),
            lambda r: replace(r, tasks=(UpdateTaskObservation("old", wrong, "running", "running"),)),
            lambda r: replace(r, desired_replicas=2, tasks=(*r.tasks, UpdateTaskObservation("old", wrong, "running", "running"))),
            lambda r: replace(r, tasks=()),
            lambda r: replace(r, rollout_state="paused"),
            lambda r: replace(r, service_name="unrelated"),
        )
        for fault in faults:
            state = self._prepare(environment=self._pins(("swagger",)))
            original = state.fresh
            observer = self._observer(state, fault=lambda r: fault(r) if r.service_name == "swagger-nginx" else r)
            with self.assertRaises(LifecycleStateError):
                await state.observe_new_components(observer)
            self.assertEqual(observer.observe.await_count, 4)
            self.assertEqual(state.fresh, original)
            self.assertEqual(state.component_inventory, original.components)
            self.assertIsNone(self.repository.load().manifest)
            with self.assertRaises(LifecycleStateError):
                state.commit()

    async def test_changed_observation_and_timeout_are_sanitized_without_commit(self):
        for failure in (UpdateObservationChanged("service_changed_during_observation"), TimeoutError("SECRET_SENTINEL")):
            state = self._prepare(environment=self._pins(("swagger",)))
            observer = Mock(spec=PortUpdateRuntimeObserver, observe=AsyncMock(side_effect=failure))
            with self.assertRaises(LifecycleStateError) as caught:
                await state.observe_new_components(observer)
            self.assertNotIn("SECRET_SENTINEL", str(caught.exception))
            self.assertIsNone(self.repository.load().manifest)
            with self.assertRaises(LifecycleStateError):
                state.commit()

    async def test_actual_async_deadline_and_cancellation_leave_fresh_inventory_unmodified(self):
        state = self._prepare(environment=self._pins(("swagger",)))
        original = state.fresh

        async def slow(*args):
            await asyncio.sleep(30)

        observer = Mock(spec=PortUpdateRuntimeObserver, observe=AsyncMock(side_effect=slow))
        with patch("tiny_swarm_world.infrastructure.adapters.lifecycle.setup_observations.OBSERVATION_TIMEOUT_SECONDS", 0.001):
            with self.assertRaises(LifecycleStateError):
                await state.observe_new_components(observer)
        self.assertEqual(state.fresh, original)
        observer.observe.side_effect = asyncio.CancelledError()
        with self.assertRaises(asyncio.CancelledError):
            await state.observe_new_components(observer)
        self.assertEqual(state.component_inventory, original.components)
        with self.assertRaises(LifecycleStateError):
            state.commit()

    async def test_stale_state_refuses_observation_and_post_observation_commit(self):
        minimal = self._prepare(())
        minimal.commit()
        state = self._prepare(environment=self._pins(("swagger",)), add=True)
        observer = self._observer(state)
        await state.observe_new_components(observer)
        snapshot = self.repository.load()
        changed = snapshot.manifest.model_copy(update={"checkpoint_reference": "concurrent-operation"})
        self.repository.save(changed, expected_token=snapshot.token)
        before = self.repository.path.read_bytes()
        with self.assertRaisesRegex(LifecycleStateError, "stale"):
            state.commit()
        observer.observe.reset_mock()
        with self.assertRaisesRegex(LifecycleStateError, "stale"):
            await state.observe_new_components(observer)
        observer.observe.assert_not_awaited()
        self.assertEqual(self.repository.path.read_bytes(), before)
