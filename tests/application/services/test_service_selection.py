from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.service_selection import ServiceSelectionService
from tiny_swarm_world.domain.lifecycle.selection import SelectionError
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tests.application.services.test_lifecycle import adoption_fixture

ROOT = Path(__file__).resolve().parents[3]


class SelectionServiceTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "state" / "manifest.json"
        self.repository = JsonManifestRepository(self.path)
        self.catalog = NativeComponentCatalog(ROOT)
        self.service = ServiceSelectionService(self.repository, self.catalog)
        self.manifest = adoption_fixture(self.catalog.load())

    def adopt(self):
        self.repository.save(self.manifest, expected_token=None)

    def test_preview_absent_state_creates_nothing(self):
        result = self.service.preview(("jenkins",))
        self.assertEqual(result.source, "explicit")
        self.assertFalse(self.path.parent.exists())
        with self.assertRaises(LifecycleStateError):
            self.service.persist(result, approved=True)
        self.assertFalse(self.path.parent.exists())

    def test_persisted_selection_authoritative_without_explicit_selection(self):
        self.adopt()
        result = self.service.preview()
        self.assertEqual(result.requested_services, self.manifest.requested_services)
        self.assertEqual(result.source, "persisted")
        self.assertEqual(result.additions, ())

    def test_add_persistence_preserves_identity_credentials_and_components(self):
        self.adopt()
        before = self.repository.load().manifest
        plan = self.service.preview(("jenkins",), add=True)
        with self.assertRaises(LifecycleStateError):
            self.service.persist(plan)
        saved = self.service.persist(plan, approved=True).manifest
        self.assertEqual(saved.installation_id, before.installation_id)
        self.assertEqual(saved.product, before.product)
        self.assertEqual(saved.credential_references, before.credential_references)
        self.assertEqual(saved.configuration_references, before.configuration_references)
        for component in before.components:
            self.assertIn(component, saved.components)
        self.assertEqual(saved.resolved_services, plan.resolved_services)
        self.assertIn("nexus", saved.resolved_services)
        self.catalog.load().validate_manifest(saved)

    def test_same_selection_is_noop_and_stale_preview_rejected(self):
        self.adopt()
        noop = self.service.preview()
        stamp = self.path.stat().st_mtime_ns
        self.service.persist(noop, approved=True)
        self.assertEqual(self.path.stat().st_mtime_ns, stamp)
        plan = self.service.preview(("jenkins",), add=True)
        self.service.persist(self.service.preview(("pulsar",), add=True), approved=True)
        with self.assertRaisesRegex(LifecycleStateError, "stale"):
            self.service.persist(plan, approved=True)

    def test_removal_reverse_dependency_preview_retains_state_and_data(self):
        self.adopt()
        self.service.persist(self.service.preview(("jenkins",), add=True), approved=True)
        before = self.path.read_bytes()
        plan = self.service.preview(remove=("nexus",))
        self.assertEqual(plan.removal_impact, {"nexus": ("jenkins",)})
        self.assertTrue(plan.retained_data)
        with self.assertRaisesRegex(LifecycleStateError, "Removal apply"):
            self.service.persist(plan, approved=True)
        implicit = self.service.preview(minimal=True)
        with self.assertRaises(LifecycleStateError):
            self.service.persist(implicit, approved=True)
        self.assertEqual(self.path.read_bytes(), before)

    def test_add_requires_existing_state_and_failure_does_not_claim_success(self):
        with self.assertRaises(SelectionError):
            self.service.preview(("jenkins",), add=True)
        self.adopt()
        repository = Mock(wraps=self.repository)
        repository.save.side_effect = LifecycleStateError("write failed")
        service = ServiceSelectionService(repository, self.catalog)
        with self.assertRaisesRegex(LifecycleStateError, "write failed"):
            service.persist(service.preview(("jenkins",), add=True), approved=True)

    def test_tampered_plan_is_rejected(self):
        self.adopt()
        plan = self.service.preview(("jenkins",), add=True)
        with self.assertRaisesRegex(LifecycleStateError, "changed"):
            self.service.persist(plan.model_copy(update={"selection_reasons": {}}), approved=True)

    def test_minimal_selection_can_be_persisted_and_repeated(self):
        self.adopt()
        saved = self.service.persist(self.service.preview(minimal=True), approved=True)
        self.assertEqual(saved.manifest.requested_services, ())
        self.assertEqual(saved.manifest.resolved_services, ("incus", "portainer"))
        stamp = self.path.stat().st_mtime_ns
        self.service.persist(self.service.preview(), approved=True)
        self.assertEqual(self.path.stat().st_mtime_ns, stamp)

    def test_changed_resources_in_catalog_block_persistence(self):
        self.adopt()
        catalog = Mock(wraps=self.catalog)
        service = ServiceSelectionService(self.repository, catalog)
        plan = service.preview(("jenkins",), add=True)
        original = self.catalog.load()
        changed_services = tuple(item.model_copy(update={"resources": item.resources.model_copy(update={
            "declared": {"changed": {"limits": {"memory": "2GiB"}}}})})
                                 if item.service_id == "jenkins" else item for item in original.services)
        catalog.load.return_value = original.model_copy(update={"services": changed_services})
        with self.assertRaisesRegex(LifecycleStateError, "changed"):
            service.persist(plan, approved=True)
