"""A private native allocation fits the measured host without relaxing admission."""
from dataclasses import replace
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from ruamel.yaml import YAML

from tiny_swarm_world.domain.preflight.resources import (
    HostResources, PlannedContainerLimit, validate_planned_container_limits,
)
from tiny_swarm_world.infrastructure.adapters.clients.lxc.resource.resolution import (
    resource_cpu, resource_memory_bytes,
)
from tiny_swarm_world.infrastructure.adapters.repositories.node_provider_config_yaml_repository import (
    NodeProviderConfig, NodeProviderConfigYamlRepository,
)
from tiny_swarm_world.infrastructure.project_paths import ProjectPaths


ROOT = Path(__file__).resolve().parents[4]
PROVIDER_RELATIVE_PATH = Path("config/node-providers/provider_config.yaml")
SOURCE_CONFIG = ROOT / "infra" / PROVIDER_RELATIVE_PATH
GIB = 1024**3
NATIVE_MEMORY_BYTES = 20_111_052_800
NATIVE_ALLOCATION = {
    "swarm-manager": "10GiB",
    "swarm-worker-1": "6GiB",
    "swarm-worker-2": "1GiB",
}


def planned_limits(config: NodeProviderConfig) -> tuple[PlannedContainerLimit, ...]:
    return tuple(PlannedContainerLimit(
        node.spec.name, resource_cpu(node.resources.get("cpu")),
        resource_memory_bytes(node.resources.get("memory")),
    ) for node in config.nodes)


class NativeResourceBudgetTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.private_infra = Path(temporary.name) / "native-infra"
        self.private_config = self.private_infra / PROVIDER_RELATIVE_PATH
        self.private_config.parent.mkdir(parents=True)
        shutil.copy2(SOURCE_CONFIG, self.private_config)
        self.source_before = SOURCE_CONFIG.read_bytes()
        self.baseline = NodeProviderConfigYamlRepository(path=SOURCE_CONFIG).load()
        self.resources = HostResources(8, NATIVE_MEMORY_BYTES, None, 0, 200 * GIB)

    def compact_config(self) -> NodeProviderConfig:
        yaml = YAML()
        payload = yaml.load(self.private_config.read_text(encoding="utf-8"))
        for node in payload["nodes"]:
            node["resources"]["memory"] = NATIVE_ALLOCATION[node["name"]]
        with self.private_config.open("w", encoding="utf-8") as stream:
            yaml.dump(payload, stream)
        with patch.dict(os.environ, {
            "TSW_REPOSITORY_ROOT": str(ROOT),
            "TSW_INFRA_ROOT": str(self.private_infra),
        }, clear=True):
            paths = ProjectPaths.from_environment()
            self.assertEqual(paths.infra_root, self.private_infra.resolve())
            repository = NodeProviderConfigYamlRepository()
            self.assertEqual(repository.path, self.private_config.resolve())
            return repository.load()

    def test_default_nineteen_gib_remains_rejected_on_measured_native_host(self):
        planned = planned_limits(self.baseline)

        self.assertEqual(sum(node.memory_bytes for node in planned), 19 * GIB)
        self.assertEqual(sum(node.cpu_threads for node in planned), 8)
        self.assertFalse(validate_planned_container_limits(self.resources, planned))

    def test_private_seventeen_gib_config_passes_and_preserves_other_authorities(self):
        compact = self.compact_config()
        planned = planned_limits(compact)

        self.assertEqual(sum(node.memory_bytes for node in planned), 17 * GIB)
        self.assertEqual(sum(node.cpu_threads for node in planned), 8)
        self.assertTrue(validate_planned_container_limits(self.resources, planned))
        self.assertEqual(replace(compact, nodes=self.baseline.nodes), self.baseline)
        self.assertEqual(len(compact.nodes), 3)
        for previous, current in zip(self.baseline.nodes, compact.nodes, strict=True):
            self.assertEqual(replace(current, resources=previous.resources), previous)
            self.assertEqual(dict(current.resources), {
                **previous.resources, "memory": NATIVE_ALLOCATION[current.spec.name],
            })
        self.assertEqual(SOURCE_CONFIG.read_bytes(), self.source_before)
        self.assertEqual(NodeProviderConfigYamlRepository(path=SOURCE_CONFIG).load(), self.baseline)

    def test_exact_measured_capacity_passes_but_byte_and_cpu_overflow_fail(self):
        planned = planned_limits(self.compact_config())
        remaining = NATIVE_MEMORY_BYTES - sum(node.memory_bytes for node in planned)
        exact = (replace(planned[0], memory_bytes=planned[0].memory_bytes + remaining), *planned[1:])

        self.assertTrue(validate_planned_container_limits(self.resources, exact))
        for first in (
            replace(exact[0], memory_bytes=exact[0].memory_bytes + 1),
            replace(exact[0], cpu_threads=exact[0].cpu_threads + 1),
        ):
            with self.subTest(first=first):
                self.assertFalse(validate_planned_container_limits(self.resources, (first, *exact[1:])))

    def test_compact_plan_respects_physical_and_cgroup_boundaries(self):
        planned = planned_limits(self.compact_config())
        required = sum(node.memory_bytes for node in planned)

        self.assertTrue(validate_planned_container_limits(
            replace(self.resources, memory_bytes=required), planned,
        ))
        self.assertFalse(validate_planned_container_limits(
            replace(self.resources, memory_bytes=required - 1), planned,
        ))
        self.assertTrue(validate_planned_container_limits(
            replace(self.resources, cgroup_memory_limit_bytes=required), planned,
        ))
        self.assertFalse(validate_planned_container_limits(
            replace(self.resources, cgroup_memory_limit_bytes=required - 1), planned,
        ))

    def test_large_cgroup_limit_does_not_inflate_physical_memory(self):
        resources = replace(self.resources, cgroup_memory_limit_bytes=64 * GIB)

        self.assertEqual(resources.effective_memory_bytes, NATIVE_MEMORY_BYTES)
        self.assertFalse(validate_planned_container_limits(resources, planned_limits(self.baseline)))
