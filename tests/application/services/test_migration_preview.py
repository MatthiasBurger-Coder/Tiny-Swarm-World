"""Read-only migration projection tests."""
from __future__ import annotations

import json
import unittest
from unittest.mock import Mock

from tests.domain.lifecycle.test_manifest_v2 import fixtures, service
from tiny_swarm_world.application.ports.lifecycle import ManifestSnapshot
from tiny_swarm_world.application.services.migration_preview import MigrationPreviewService


class MigrationPreviewServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest, self.catalog_value = fixtures(("swagger", "nexus"))
        self.manifests = Mock()
        self.catalog = Mock()
        self.manifests.load.return_value = ManifestSnapshot(
            self.manifest, "secret-token", ("secret-diagnostic /private/path",))
        self.catalog.load.return_value = self.catalog_value
        self.service = MigrationPreviewService(self.manifests, self.catalog)

    def test_projection_has_only_closed_redacted_fields_and_sorted_policy(self) -> None:
        result = self.service.preview()
        self.assertEqual(result, {
            "status": "PREVIEW", "source": "operator_local_unverified", "applied": False, "qualified": False,
            "project": "UNKNOWN", "profile": "UNKNOWN", "route": "UNKNOWN", "owner": "UNKNOWN",
            "swagger_exposure": "published",
            "stack_policies": [{"service_id": "nexus", "owner": "swarm"},
                               {"service_id": "swagger", "owner": "swarm"}],
        })
        encoded = json.dumps(result)
        for forbidden in ("secret", "/private", "credential", "configuration", "12345678", "product", "snapshot"):
            self.assertNotIn(forbidden, encoded)
        self.manifests.save.assert_not_called()
        self.assertEqual(self.service.preview(), result)

    def test_missing_manifest_and_port_failures_never_save(self) -> None:
        self.manifests.load.return_value = ManifestSnapshot(None, "secret", ("private",))
        with self.assertRaises(ValueError):
            self.service.preview()
        self.catalog.load.assert_not_called()
        self.manifests.save.assert_not_called()
        self.manifests.load.side_effect = PermissionError("SECRET /private/path")
        with self.assertRaises(PermissionError):
            self.service.preview()
        self.manifests.save.assert_not_called()

    def test_attacker_supplied_known_syntax_id_is_rejected_before_projection(self) -> None:
        evil = service("secret-service", "stack", dependencies=("portainer",))
        self.catalog.load.return_value = self.catalog_value.model_copy(
            update={"services": self.catalog_value.services + (evil,)})
        with self.assertRaises(ValueError):
            self.service.preview()
        self.manifests.save.assert_not_called()

    def test_forged_or_ambiguous_catalog_and_manifest_are_blocked(self) -> None:
        self.catalog.load.return_value = self.catalog_value.model_copy(
            update={"services": self.catalog_value.services + (self.catalog_value.services[0],)})
        with self.assertRaises(ValueError):
            self.service.preview()
        self.catalog.load.return_value = self.catalog_value
        self.manifests.load.return_value = ManifestSnapshot(
            self.manifest.model_copy(update={"schema_version": 2}), "secret", ())
        with self.assertRaises(ValueError):
            self.service.preview()
        self.manifests.save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
