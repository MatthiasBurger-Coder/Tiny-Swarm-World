from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.application.services.lifecycle import InstallationLifecycleService
from tiny_swarm_world.infrastructure.adapters.lifecycle.catalog import NativeComponentCatalog
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tests.domain.lifecycle.test_models import manifest_fixture

ROOT = Path(__file__).resolve().parents[3]


def adoption_fixture(catalog):
    manifest = manifest_fixture()
    services = {service.service_id: service for service in catalog.services}
    return manifest.model_copy(update={"components": tuple(component for name in manifest.resolved_services for component in services[name].components)})


class LifecycleServiceTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "new" / "manifest.json"
        self.repository = JsonManifestRepository(self.path)
        self.catalog = NativeComponentCatalog(ROOT)
        self.service = InstallationLifecycleService(self.repository, self.catalog)
        self.manifest = adoption_fixture(self.catalog.load())

    def test_inspection_and_adoption_preview_do_not_mutate(self):
        result = self.service.inspect()
        self.assertEqual(result["status"], "adoption_required")
        preview = self.service.adopt(self.manifest)
        self.assertEqual(preview.manifest, self.manifest)
        self.assertFalse(self.path.parent.exists())

    def test_adoption_requires_approval_and_repeat_is_noop(self):
        with self.assertRaises(LifecycleStateError):
            self.service.adopt(self.manifest, preview=False)
        self.assertFalse(self.path.exists())
        first = self.service.adopt(self.manifest, preview=False, approved=True)
        timestamp = self.path.stat().st_mtime_ns
        self.assertEqual(self.service.adopt(self.manifest, preview=False, approved=True), first)
        self.assertEqual(timestamp, self.path.stat().st_mtime_ns)
        result = self.service.inspect()
        self.assertTrue(all(component["drift"] == ["observation_missing"] for component in result["components"]))
        self.assertNotIn("verified", result["status"])

    def test_ambiguous_or_incomplete_inventory_is_rejected(self):
        for changed in (
            self.manifest.model_copy(update={"components": ()}),
            self.manifest.model_copy(update={"resolved_services": ("incus", "portainer", "unknown")}),
        ):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                self.service.adopt(changed, preview=False, approved=True)
        self.assertFalse(self.path.exists())

    def test_adoption_cannot_replace_existing_identity(self):
        self.service.adopt(self.manifest, preview=False, approved=True)
        other = adoption_fixture(self.catalog.load())
        with self.assertRaises(LifecycleStateError):
            self.service.adopt(other, preview=False, approved=True)
        self.assertEqual(self.repository.load().manifest, self.manifest)

    def test_interrupted_adoption_requires_operator_inspection(self):
        self.path.parent.mkdir()
        (self.path.parent / ".installation-manifest-orphan.tmp").write_text("{}")
        with self.assertRaises(LifecycleStateError):
            self.service.adopt(self.manifest, preview=False, approved=True)

    def test_persistence_failure_propagates_without_claiming_success(self):
        manifests = Mock(wraps=self.repository)
        manifests.save.side_effect = LifecycleStateError("write failed")
        service = InstallationLifecycleService(manifests, self.catalog)
        with self.assertRaises(LifecycleStateError):
            service.adopt(self.manifest, preview=False, approved=True)

    def test_dependency_and_preset_rejection(self):
        payload = self.manifest.model_copy(update={"requested_services": ("incus", "portainer", "jenkins"), "resolved_services": ("incus", "portainer", "jenkins")})
        with self.assertRaisesRegex(ValueError, "dependencies"):
            self.catalog.load().validate_manifest(payload)
        payload = self.manifest.model_copy(update={"resolved_services": ("incus", "portainer", "infisical")})
        with self.assertRaisesRegex(ValueError, "preset"):
            self.catalog.load().validate_manifest(payload)
