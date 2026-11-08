import tempfile
import unittest
from pathlib import Path

from tiny_swarm_world.domain.configuration.secret_manifest import SecretManifestValidationError
from tiny_swarm_world.infrastructure.adapters.repositories.secret_manifest_yaml_repository import SecretManifestYamlRepository


class TestSecretManifestYamlRepository(unittest.TestCase):
    def load(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.yaml"
            path.write_text(text, encoding="utf-8")
            return SecretManifestYamlRepository(path).load()

    def test_valid_defaults_and_unknown_source(self):
        entry, = self.load("secrets:\n- key: TSW_TEST_PASSWORD\n  type: managed_secret\n  source: reserved_source\n")
        self.assertFalse(entry.required)
        self.assertEqual(entry.environment, "local")
        self.assertEqual(entry.owner, "unknown")
        self.assertEqual(entry.policy, "keep_existing")
        self.assertIs(type(entry.key), str)

    def test_malformed_documents_fail_without_echoing_values(self):
        entry = "key: TSW_TEST_PASSWORD\n  type: managed_secret\n  source: internal_test_catalog"
        documents = [
            "", "[]", "secrets: {}", "secrets: [null]", "secrets: [sensitive-marker]",
            "secrets: [", "secrets: []\nsecrets: []", "secrets: []\n1: value", "secrets: []\n---\nsecrets: []",
            f"secrets:\n- {entry}\n  required: 'false'",
            f"secrets:\n- {entry}\n  required: 1",
            f"secrets:\n- {entry}\n  service: [sensitive-marker]",
            f"secrets:\n- {entry}\n  key: TSW_OTHER_PASSWORD",
            f"secrets:\n- {entry}\n- {entry}",
            "secrets:\n- key: sensitive-marker\n  type: managed_secret\n  source: internal_test_catalog",
            "secrets:\n- key: TSW_TEST_PASSWORD\n  type: managed_secret",
        ]
        for document in documents:
            with self.subTest(document=document):
                with self.assertRaises(SecretManifestValidationError) as caught:
                    self.load(document)
                self.assertNotIn("sensitive-marker", str(caught.exception))

    def test_safe_loader_boolean_and_merge_compatibility(self):
        entries = self.load("secrets:\n- &base\n  key: TSW_ONE_PASSWORD\n  type: managed_secret\n  source: internal_test_catalog\n  required: yes\n- <<: *base\n  key: TSW_TWO_PASSWORD\n  required: no\n")
        self.assertTrue(entries[0].required)
        self.assertFalse(entries[1].required)
        self.assertEqual(entries[1].source, "internal_test_catalog")

    def test_missing_file_is_safe_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(SecretManifestValidationError):
                SecretManifestYamlRepository(Path(directory) / "missing.yaml").load()

    def test_committed_manifest_preserves_entries(self):
        entries = SecretManifestYamlRepository().load()
        self.assertGreater(len(entries), 10)
        self.assertEqual(len(entries), len({entry.key for entry in entries}))
