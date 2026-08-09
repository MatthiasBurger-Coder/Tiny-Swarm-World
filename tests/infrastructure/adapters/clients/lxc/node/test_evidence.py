import ast
import unittest
from pathlib import Path

from tiny_swarm_world.infrastructure.adapters.clients.lxc.node.evidence import (
    EvidenceBuilder,
    EvidenceKey,
)


class TestEvidenceBuilder(unittest.TestCase):
    def test_serializes_typed_keys_and_scalar_values(self):
        evidence = (
            EvidenceBuilder()
            .add(EvidenceKey.PHASE, "pre_apply")
            .add(EvidenceKey.RETURN_CODE, 2)
            .add(EvidenceKey.TIMED_OUT, True)
            .add("optional", False)
            .build()
        )

        self.assertEqual(
            {
                "phase": "pre_apply",
                "return_code": "2",
                "timed_out": "true",
                "optional": "false",
            },
            evidence,
        )

    def test_omits_none_values_and_keeps_empty_strings(self):
        evidence = (
            EvidenceBuilder()
            .add(EvidenceKey.BACKEND, None)
            .add("available_profiles", "")
            .build()
        )

        self.assertEqual({"available_profiles": ""}, evidence)

    def test_build_returns_an_isolated_copy(self):
        builder = EvidenceBuilder().add(EvidenceKey.CLASSIFICATION, "ready")

        first = builder.build()
        first["classification"] = "changed"

        self.assertEqual({"classification": "ready"}, builder.build())


class TestEvidenceBuilderBoundary(unittest.TestCase):
    def test_builder_has_no_runtime_or_application_dependencies(self):
        source_path = (
            Path(__file__).parents[6]
            / "src"
            / "tiny_swarm_world"
            / "infrastructure"
            / "adapters"
            / "clients"
            / "lxc"
            / "node"
            / "evidence.py"
        )
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        imported_modules.update(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )

        self.assertFalse(any(module.startswith("asyncio") for module in imported_modules))
        self.assertFalse(any(module.startswith("subprocess") for module in imported_modules))
        self.assertFalse(
            any(module.startswith("tiny_swarm_world.application") for module in imported_modules)
        )
        self.assertFalse(
            any(module.startswith("tiny_swarm_world.domain") for module in imported_modules)
        )
