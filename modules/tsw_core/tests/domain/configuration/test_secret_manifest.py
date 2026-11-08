import unittest
from dataclasses import FrozenInstanceError, replace

from tiny_swarm_world.domain.configuration.secret_manifest import SecretManifestEntry, SecretManifestValidationError


class TestSecretManifest(unittest.TestCase):
    def entry(self):
        return SecretManifestEntry(key="TSW_TEST_PASSWORD", service="test", type="managed_secret", environment="local", description="", source="internal_test_catalog", required=True)

    def test_model_is_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            self.entry().required = False

    def test_model_rejects_invalid_values(self):
        for changes in ({"required": "false"}, {"key": "bad"}, {"type": "removed"}, {"policy": "bad"}, {"source": ""}, {"service": None}, {"source": "external_user_secret"}):
            with self.subTest(changes=changes), self.assertRaises(SecretManifestValidationError):
                replace(self.entry(), **changes)
