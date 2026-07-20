import tempfile
import unittest
from pathlib import Path

from tiny_swarm_world.infrastructure.adapters.host.preflight_evidence_writer import PreflightEvidenceWriter


class PreflightEvidenceWriterTests(unittest.TestCase):
    def test_writes_structured_evidence_inside_root(self):
        with tempfile.TemporaryDirectory() as directory:
            target = PreflightEvidenceWriter(Path(directory)).write(
                {"status": "SUPPORTED", "host_resources": {"cpu": 8}},
                ".tiny-swarm-world/evidence/preflight.json",
            )
            self.assertTrue(target.exists())
            self.assertIn('"status": "SUPPORTED"', target.read_text())

    def test_rejects_path_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                PreflightEvidenceWriter(Path(directory)).write({}, "../outside.json")

