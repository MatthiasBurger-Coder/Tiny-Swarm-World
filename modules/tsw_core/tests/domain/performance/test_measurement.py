import unittest
from typing import Any

from tiny_swarm_world.domain.performance import PerformanceMeasurement


class TestPerformanceMeasurement(unittest.TestCase):
    def test_serializes_optional_values_and_sorted_fields_deterministically(self):
        measurement = PerformanceMeasurement(
            issue_id="issue-145",
            workflow_id="issue-152-20260809",
            segment_id="setup-phase-group",
            segment="Setup phase group",
            measurement_scope="mocked",
            target_kind="phase_group",
            target_ids=("worker-b", "manager", "worker-a"),
            environment_summary="native-linux-local",
            counters={"max_concurrency": 4, "phase_count": 2},
            baseline={"duration_seconds": 4.0},
            new_values={"duration_seconds": 2.0},
            limitations=(
                "local scheduler timing is not globally absolute",
                "mocked operations do not represent live runtime",
            ),
        )

        self.assertEqual(
            measurement.to_dict(),
            {
                "baseline": {"duration_seconds": 4.0},
                "counters": {"max_concurrency": 4, "phase_count": 2},
                "duration_seconds": None,
                "environment_summary": "native-linux-local",
                "finished_at": None,
                "issue_id": "issue-145",
                "limitations": [
                    "local scheduler timing is not globally absolute",
                    "mocked operations do not represent live runtime",
                ],
                "measurement_scope": "mocked",
                "new_values": {"duration_seconds": 2.0},
                "segment": "Setup phase group",
                "segment_id": "setup-phase-group",
                "started_at": None,
                "target_ids": ["manager", "worker-a", "worker-b"],
                "target_kind": "phase_group",
                "workflow_id": "issue-152-20260809",
            },
        )

    def test_accepts_timezone_timestamps_and_single_target(self):
        measurement = PerformanceMeasurement(
            issue_id="issue-144",
            workflow_id="issue-144-run-1",
            segment_id="install-readiness-wait",
            segment="Readiness wait",
            measurement_scope="local",
            target_kind="single_computer",
            target_ids=("host",),
            environment_summary="wsl-local",
            started_at="2026-08-11T10:00:00+00:00",
            finished_at="2026-08-11T10:00:01+00:00",
            duration_seconds=1,
            limitations=("local timing is comparative only",),
        )

        self.assertEqual(measurement.duration_seconds, 1.0)
        self.assertEqual(measurement.target_ids, ("host",))

    def test_rejects_unsafe_context_and_measurement_text(self):
        with self.assertRaisesRegex(ValueError, "unsafe"):
            _measurement(environment_summary="host_ip=10.0.0.1")
        with self.assertRaisesRegex(ValueError, "unsafe"):
            _measurement(new_values={"result": "sudo docker ps"})

    def test_rejects_invalid_numbers_timestamps_targets_and_missing_limitations(self):
        invalid_values = (
            {"duration_seconds": -1},
            {"counters": {"calls": -1}},
            {"started_at": "2026-08-11T10:00:00"},
            {"target_ids": ()},
            {"limitations": ()},
        )
        for overrides in invalid_values:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    _measurement(**overrides)


def _measurement(**overrides: Any) -> PerformanceMeasurement:
    values: dict[str, Any] = {
        "issue_id": "issue-152",
        "workflow_id": "issue-152-20260809",
        "segment_id": "contract",
        "segment": "Performance contract",
        "measurement_scope": "mocked",
        "target_kind": "single_computer",
        "target_ids": ("host",),
        "environment_summary": "native-linux-local",
        "limitations": ("local timing is comparative only",),
    }
    values.update(overrides)
    return PerformanceMeasurement(**values)
