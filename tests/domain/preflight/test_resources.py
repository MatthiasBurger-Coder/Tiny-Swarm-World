import tempfile
import unittest
from unittest.mock import patch
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
    def _root(self, meminfo: str, *, current: str = "100", maximum: str = "max", high: str = "max", events: str = "") -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / "proc").mkdir(parents=True)
        (root / "sys/fs/cgroup").mkdir(parents=True)
        (root / "proc/meminfo").write_text(meminfo)
        (root / "sys/fs/cgroup/memory.current").write_text(current)
        (root / "sys/fs/cgroup/memory.max").write_text(maximum)
        (root / "sys/fs/cgroup/memory.high").write_text(high)
        (root / "sys/fs/cgroup/memory.events").write_text(events)
        return root

    def test_inspect_reads_meminfo_cgroup_and_disk(self):
        root = self._root("MemTotal: 1024 kB\n", current="22", maximum="2048")
        with patch("tiny_swarm_world.infrastructure.adapters.host.wsl_resource_inspector.os.cpu_count", return_value=4):
            result = WslResourceInspector(root).inspect()

        self.assertEqual(4, result.cpu_threads)
        self.assertEqual(1024 * 1024, result.memory_bytes)
        self.assertEqual(2048, result.cgroup_memory_limit_bytes)
        self.assertEqual(22, result.current_memory_usage_bytes)
        self.assertGreater(result.free_disk_bytes, 0)

    def test_memory_pressure_classifies_high_and_near_max(self):
        high_root = self._root("MemTotal: 1 kB\n", current="100", maximum="1000", high="50")
        self.assertEqual("memory_high_pressure", WslResourceInspector(high_root).memory_pressure().assessment)

        near_root = self._root("MemTotal: 1 kB\n", current="96", maximum="100", high="max")
        self.assertEqual("critical_memory_pressure", WslResourceInspector(near_root).memory_pressure().assessment)

    def test_missing_and_invalid_values_are_safe(self):
        root = self._root("MemTotal: invalid\n", current="invalid", maximum="", high="invalid")
        report = WslResourceInspector(root).memory_pressure()
        self.assertEqual("no_confirmed_memory_pressure", report.assessment)
        self.assertIsNone(report.memory_max)

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
