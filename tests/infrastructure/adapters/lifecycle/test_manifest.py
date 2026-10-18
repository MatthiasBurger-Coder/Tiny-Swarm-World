from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tiny_swarm_world.application.ports.lifecycle import LifecycleStateError
from tiny_swarm_world.infrastructure.adapters.lifecycle.manifest import JsonManifestRepository
from tests.domain.lifecycle.test_models import manifest_fixture


class JsonManifestRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.path = self.root / "private" / "manifest.json"
        self.repository = JsonManifestRepository(self.path)

    def test_missing_read_creates_nothing(self):
        self.assertIsNone(self.repository.load().manifest)
        self.assertFalse(self.path.parent.exists())

    def test_atomic_roundtrip_noop_and_unrelated_configuration(self):
        unrelated = self.root / "operator.yaml"
        unrelated.write_text("override: keep\n")
        manifest = manifest_fixture()
        first = self.repository.save(manifest, expected_token=None)
        stat = self.path.stat()
        again = self.repository.save(manifest, expected_token=first.token)
        self.assertEqual(first, again)
        self.assertEqual(stat.st_mtime_ns, self.path.stat().st_mtime_ns)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(unrelated.read_text(), "override: keep\n")
        with self.assertRaises(LifecycleStateError):
            self.repository.save(manifest, expected_token=None)

    def test_interruption_before_replace_preserves_original(self):
        original = manifest_fixture()
        first = self.repository.save(original, expected_token=None)
        content = self.path.read_bytes()
        changed = original.model_copy(update={"checkpoint_reference": "operation-2"})
        with patch("tiny_swarm_world.infrastructure.adapters.lifecycle.manifest.os.replace", side_effect=OSError("SECRET_SENTINEL")):
            with self.assertRaises(LifecycleStateError) as caught:
                self.repository.save(changed, expected_token=first.token)
        self.assertNotIn("SECRET_SENTINEL", str(caught.exception))
        self.assertEqual(content, self.path.read_bytes())
        self.assertFalse(list(self.path.parent.glob("*.tmp")))

    def test_fsync_before_replace_preserves_original(self):
        first = self.repository.save(manifest_fixture(), expected_token=None)
        before = self.path.read_bytes()
        with patch("tiny_swarm_world.infrastructure.adapters.lifecycle.manifest.os.fsync", side_effect=OSError("disk full")):
            with self.assertRaises(LifecycleStateError):
                self.repository.save(first.manifest.model_copy(update={"checkpoint_reference": "next"}), expected_token=first.token)
        self.assertEqual(before, self.path.read_bytes())

    def test_durability_failure_after_replace_requires_inspection(self):
        first = self.repository.save(manifest_fixture(), expected_token=None)
        changed = first.manifest.model_copy(update={"checkpoint_reference": "next"})
        with patch("tiny_swarm_world.infrastructure.adapters.lifecycle.manifest.os.fsync", side_effect=[None, OSError("directory fsync")]):
            with self.assertRaises(LifecycleStateError):
                self.repository.save(changed, expected_token=first.token)
        self.assertEqual(self.repository.load().manifest, changed)

    def test_orphan_temporary_file_is_diagnostic_and_never_adopted(self):
        self.path.parent.mkdir()
        pending = self.path.parent / ".installation-manifest-crash.tmp"
        pending.write_text(manifest_fixture().model_dump_json())
        snapshot = self.repository.load()
        self.assertIsNone(snapshot.manifest)
        self.assertTrue(snapshot.diagnostics[0].startswith("interrupted_write"))
        self.assertTrue(pending.exists())

    def test_unknown_and_corrupt_state_never_overwritten(self):
        self.path.parent.mkdir()
        for content in ('{"schema_version":999}', '{"password":"SECRET_SENTINEL"}', '{broken'):
            self.path.write_text(content)
            with self.assertRaises(LifecycleStateError):
                self.repository.save(manifest_fixture(), expected_token=None)
            self.assertEqual(self.path.read_text(), content)

    def test_symlink_is_refused(self):
        self.path.parent.mkdir()
        target = self.root / "target"
        target.write_text(manifest_fixture().model_dump_json())
        self.path.symlink_to(target)
        with self.assertRaises(LifecycleStateError):
            self.repository.load()
