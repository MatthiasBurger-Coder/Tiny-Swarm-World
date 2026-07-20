import tempfile
import unittest
from pathlib import Path

from tiny_swarm_world.domain.preflight.resources import (
    HostResources,
    ResourceAssessment,
    ResourceRequirements,
    PlannedContainerLimit,
    assess_resources,
    validate_planned_container_limits,
    validate_container_limits,
)
from tiny_swarm_world.infrastructure.adapters.host.wsl_resource_inspector import WslResourceInspector


class ResourceAssessmentTests(unittest.TestCase):
    def test_below_minimum_is_insufficient(self):
        resources = HostResources(4, 8 * 1024**3, 8 * 1024**3, 0, 200 * 1024**3)
        result = assess_resources(resources, ResourceRequirements(8, 16 * 1024**3, 150 * 1024**3))
        self.assertEqual(result.assessment, ResourceAssessment.INSUFFICIENT)

    def test_minimum_and_recommendation_are_distinguished(self):
        resources = HostResources(8, 16 * 1024**3, 16 * 1024**3, 0, 150 * 1024**3)
        result = assess_resources(
            resources,
            ResourceRequirements(8, 16 * 1024**3, 150 * 1024**3),
            recommended=ResourceRequirements(12, 24 * 1024**3, 250 * 1024**3),
        )
        self.assertEqual(result.assessment, ResourceAssessment.SUPPORTED_WITH_WARNINGS)

    def test_container_limits_do_not_exceed_effective_capacity(self):
        resources = HostResources(8, 16 * 1024**3, 16 * 1024**3, 0, 0)
        self.assertFalse(validate_container_limits(resources, 4, 8 * 1024**3, 8, 10 * 1024**3))

    def test_planned_container_limits_are_aggregated(self):
        resources = HostResources(8, 16 * 1024**3, 16 * 1024**3, 0, 0)
        planned = (
            PlannedContainerLimit("manager", 4, 8 * 1024**3),
            PlannedContainerLimit("worker", 4, 8 * 1024**3),
        )
        self.assertTrue(validate_planned_container_limits(resources, planned))
        self.assertFalse(
            validate_planned_container_limits(
                resources, (*planned, PlannedContainerLimit("extra", 1, 1))
            )
        )


class WslResourceInspectorTests(unittest.TestCase):
    def test_parses_cgroup_max_and_memory_events(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "proc").mkdir(parents=True)
            (root / "sys/fs/cgroup").mkdir(parents=True)
            (root / "proc/meminfo").write_text("MemTotal:       16777216 kB\n")
            (root / "sys/fs/cgroup/memory.max").write_text("max\n")
            (root / "sys/fs/cgroup/memory.current").write_text("100\n")
            (root / "sys/fs/cgroup/memory.high").write_text("max\n")
            (root / "sys/fs/cgroup/memory.events").write_text("oom 0\noom_kill 1\n")
            report = WslResourceInspector(root).memory_pressure()
            self.assertEqual(report.assessment, "oom_kill_detected")
            self.assertIsNone(report.memory_max)
