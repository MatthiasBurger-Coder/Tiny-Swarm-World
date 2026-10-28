from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock

from tests.domain.lifecycle.test_update_planning import update_fixture
from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError, ManifestSnapshot
from tiny_swarm_world.application.services.component_updates import ComponentUpdateService
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository


class ComponentUpdateServiceTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "manifest.json"
        self.catalog, self.manifest = update_fixture()
        self.repository = JsonManifestRepository(self.path)
        self.repository.save(self.manifest, expected_token=None)
        self.manifests = Mock(wraps=self.repository)
        self.catalogs = Mock()
        self.catalogs.load.return_value = self.catalog
        self.service = ComponentUpdateService(self.manifests, self.catalogs)

    def test_discover_and_preview_preserve_all_state(self):
        before = {item.name: (item.read_bytes(), item.stat().st_mtime_ns) for item in self.path.parent.iterdir()}
        found = self.service.discover()
        self.assertEqual({item["service_id"] for item in found["services"]}, set(self.manifest.resolved_services))
        self.assertEqual(found["observation_source"], "recorded-manifest-not-live")
        self.assertIn("offline", found["metadata_status"])
        result = self.service.preview(("jenkins", "nexus"))
        self.assertEqual(result.status, "preview")
        self.assertEqual(result.manifest_token, self.repository.load().token)
        self.manifests.save.assert_not_called()
        self.assertEqual(before, {item.name: (item.read_bytes(), item.stat().st_mtime_ns) for item in self.path.parent.iterdir()})

    def test_discovery_fixed_target_does_not_admit_tag_only_native_source(self):
        catalog, manifest = update_fixture(("swagger",), qualified=False)
        self.catalogs.load.return_value = catalog
        self.manifests.load.return_value = ManifestSnapshot(manifest, "token")
        found = self.service.discover(("swagger",))
        item = found["services"][0]
        self.assertEqual(item["available_supported_targets"], [])
        self.assertEqual(self.service.preview(("swagger",)).status, "blocked")
        self.assertIn("candidate-transition",
                      [target["qualification"] for target in item["catalog_references"]])
        self.assertEqual(len(item["components"]), 4)
        self.assertIn("latest", item["restriction"])
        self.assertEqual({item["service_id"] for item in self.service.discover()["services"]}, set(manifest.resolved_services))

    def test_candidate_transition_is_not_advertised_or_planned(self):
        catalog, manifest = update_fixture(("swagger",))
        service = next(item for item in catalog.services if item.service_id == "swagger")
        candidate_id = service.update_transitions[0].target_id
        targets = tuple(target.model_copy(update={"qualification": "candidate-transition"})
                        if target.target_id == candidate_id else target for target in service.update_targets)
        catalog = catalog.model_copy(update={"services": tuple(
            item.model_copy(update={"update_targets": targets}) if item.service_id == "swagger" else item
            for item in catalog.services
        )})
        self.catalogs.load.return_value = catalog
        self.manifests.load.return_value = ManifestSnapshot(manifest, "token")

        found = self.service.discover(("swagger",))["services"][0]
        self.assertEqual(found["available_supported_targets"], [])
        self.assertEqual(found["catalog_references"][0]["qualification"], "candidate-transition")
        for target_id in (None, candidate_id):
            self.assertEqual(self.service.preview(("swagger",), target_id).status, "blocked")

    def test_identity_fields_and_unknown_observation_are_explicit(self):
        components = tuple(item.model_copy(update={"desired": item.desired.model_copy(update={"upstream_version": "test-upstream"}), "observed": None})
                           if item.service_id == "jenkins" else item for item in self.manifest.components)
        self.manifests.load.return_value = ManifestSnapshot(self.manifest.model_copy(update={"components": components}), "token")
        found = self.service.discover(("jenkins",))["services"][0]["components"][0]
        self.assertIsNone(found["installed"])
        self.assertEqual(found["observation_status"], "missing")
        self.assertEqual(found["digest_status"], "unavailable")
        self.assertEqual(found["desired"]["upstream_version"], "test-upstream")
        self.assertEqual(found["desired"]["image_tag"], "0.2.0")
        self.assertEqual(found["desired"]["build_identity"], "0.2.0")
        self.assertNotEqual(found["desired"]["image_digest"], found["desired"]["image_tag"])

    def test_missing_manifest_unavailable_catalog_corrupt_inventory_and_interruption(self):
        self.manifests.load.return_value = ManifestSnapshot(None, None)
        with self.assertRaisesRegex(LifecycleStateError, "adoption"):
            self.service.discover()
        self.catalogs.load.side_effect = LifecycleStateError("Catalog unavailable")
        with self.assertRaisesRegex(LifecycleStateError, "unavailable"):
            self.service.preview(("nexus",))
        self.catalogs.load.side_effect = None
        self.manifests.load.return_value = ManifestSnapshot(self.manifest.model_copy(update={"components": ()}), "token")
        with self.assertRaisesRegex(LifecycleStateError, "mismatch"):
            self.service.discover()
        self.manifests.load.return_value = ManifestSnapshot(self.manifest, "token", ("interrupted_write: inspect",))
        result = self.service.preview(("nexus",))
        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.diagnostics, ("interrupted_write: inspect",))
        self.manifests.save.assert_not_called()
