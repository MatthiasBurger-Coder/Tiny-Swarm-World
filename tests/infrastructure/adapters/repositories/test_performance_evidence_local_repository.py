import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from tiny_swarm_world.infrastructure.adapters.repositories.performance_evidence_local_repository import (
    PerformanceEvidenceLocalRepository,
)
from tiny_swarm_world.domain.performance import PerformanceMeasurement


class TestPerformanceEvidenceLocalRepository(unittest.TestCase):
    def test_writes_stable_json_and_markdown_pair(self):
        with TemporaryDirectory() as temporary_directory:
            repository = PerformanceEvidenceLocalRepository(Path(temporary_directory))

            json_path, markdown_path = repository.write(_measurement())

            expected_stem = "issue-152-20260809--setup-phase-group"
            self.assertEqual(
                json_path,
                Path(temporary_directory) / "issue-152" / f"{expected_stem}.json",
            )
            self.assertEqual(
                markdown_path,
                Path(temporary_directory) / "issue-152" / f"{expected_stem}.md",
            )
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["target_ids"], ["manager", "worker-a"])
            self.assertEqual(payload["counters"], {"max_concurrency": 2})
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertIn("## Baseline and new values", markdown)
            self.assertIn("| `duration_seconds` | 4.0 | 2.0 |", markdown)
            self.assertTrue(markdown.endswith("\n"))

    def test_repeated_write_is_byte_stable_and_optional_values_are_explicit(self):
        with TemporaryDirectory() as temporary_directory:
            repository = PerformanceEvidenceLocalRepository(Path(temporary_directory))
            measurement = _measurement(
                counters=None,
                baseline=None,
                new_values=None,
                duration_seconds=None,
            )

            json_path, markdown_path = repository.write(measurement)
            first_json = json_path.read_bytes()
            first_markdown = markdown_path.read_bytes()
            repository.write(measurement)

            self.assertEqual(first_json, json_path.read_bytes())
            self.assertEqual(first_markdown, markdown_path.read_bytes())
            payload = json.loads(first_json)
            self.assertEqual(payload["counters"], {})
            self.assertIsNone(payload["duration_seconds"])
            self.assertIn("| *(none)* | — |", first_markdown.decode("utf-8"))


def _measurement(**overrides: Any) -> PerformanceMeasurement:
    values: dict[str, Any] = {
        "issue_id": "issue-152",
        "workflow_id": "issue-152-20260809",
        "segment_id": "setup-phase-group",
        "segment": "Setup phase group",
        "measurement_scope": "mocked",
        "target_kind": "phase_group",
        "target_ids": ("worker-a", "manager"),
        "environment_summary": "native-linux-local",
        "duration_seconds": 2.0,
        "counters": {"max_concurrency": 2},
        "baseline": {"duration_seconds": 4.0},
        "new_values": {"duration_seconds": 2.0},
        "limitations": ("mocked timing is not live runtime",),
    }
    values.update(overrides)
    return PerformanceMeasurement(**values)
