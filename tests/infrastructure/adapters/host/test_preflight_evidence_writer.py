import tempfile
import unittest
from pathlib import Path

from tiny_swarm_world.infrastructure.adapters.host.preflight_evidence_writer import PreflightEvidenceWriter


class PreflightEvidenceWriterTests(unittest.TestCase):
    def test_writes_structured_evidence_inside_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "private"
            root.mkdir(mode=0o700)
            target = PreflightEvidenceWriter(root).write(
                {"status": "SUPPORTED", "host_resources": {"cpu": 8}},
                ".tiny-swarm-world/evidence/preflight.json",
            )
            self.assertTrue(target.exists())
            self.assertIn('"status": "SUPPORTED"', target.read_text())

    def test_rejects_path_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                PreflightEvidenceWriter(Path(directory)).write({}, "../outside.json")

    def test_rejects_existing_non_private_root_without_rewriting_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "evidence"
            root.mkdir(mode=0o755)

            with self.assertRaises(ValueError):
                PreflightEvidenceWriter(root).write({}, "preflight.json")

            self.assertEqual(0o755, root.stat().st_mode & 0o777)
