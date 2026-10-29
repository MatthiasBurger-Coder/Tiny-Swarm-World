"""Preview manifest port reads only its fixed path and rejects all writes."""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tests.domain.lifecycle.test_manifest_v2 import fixtures
from tiny_swarm_world.infrastructure.adapters.lifecycle.preview_file_reader import MANIFEST, PreviewFileReader
from tiny_swarm_world.infrastructure.adapters.lifecycle.preview_manifest import PreviewManifestRepository


class PreviewManifestTests(unittest.TestCase):
    def test_load_and_save_rejection(self) -> None:
        manifest, _ = fixtures()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / MANIFEST
            path.parent.mkdir(parents=True)
            path.write_text(manifest.model_dump_json(), encoding="utf-8")
            before = path.read_bytes()
            with PreviewFileReader(root) as reader:
                repo = PreviewManifestRepository(reader)
                self.assertEqual(repo.load().manifest, manifest)
                with self.assertRaises(ValueError):
                    repo.save(manifest, expected_token=None)
            self.assertEqual(path.read_bytes(), before)

    def test_missing_malformed_and_schema_two_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / MANIFEST
            path.parent.mkdir(parents=True)
            with self.assertRaises(OSError), PreviewFileReader(root) as reader:
                PreviewManifestRepository(reader).load()
            for payload in ("{bad", '{"schema_version":2}', '{"schema_version":true}'):
                with self.subTest(payload=payload):
                    path.write_text(payload, encoding="utf-8")
                    with self.assertRaises(ValueError), PreviewFileReader(root) as reader:
                        PreviewManifestRepository(reader).load()


if __name__ == "__main__":
    unittest.main()
