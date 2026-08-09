import ast
from pathlib import Path
import re
import unittest

import tiny_swarm_world.infrastructure.composition as composition


class TestLxcRuntimeBoundaries(unittest.TestCase):
    def test_backend_cli_mapping_has_one_infrastructure_source(self):
        infrastructure_root = (
            Path(__file__).parents[2]
            / "src"
            / "tiny_swarm_world"
            / "infrastructure"
        )
        mapping_sources = []
        local_mapping_definitions = []
        for source_path in infrastructure_root.rglob("*.py"):
            source = source_path.read_text(encoding="utf-8")
            if re.search(r"ManagedLxcBackend\.INCUS:\s*[\"']incus[\"']", source):
                mapping_sources.append(source_path.relative_to(infrastructure_root).as_posix())
            if re.search(r"^_\w*BACKEND_CLI\s*=", source, re.MULTILINE):
                local_mapping_definitions.append(source_path.relative_to(infrastructure_root).as_posix())

        self.assertEqual(mapping_sources, ["adapters/clients/lxc/command/backend_cli.py"])
        self.assertEqual(local_mapping_definitions, [])

    def test_composition_uses_extracted_concrete_modules(self):
        self.assertEqual(
            composition.LxcContainerRuntime.__module__,
            "tiny_swarm_world.infrastructure.adapters.clients.lxc.docker.lxc_container_runtime",
        )
        self.assertEqual(
            composition.LxcContainerImagePublisher.__module__,
            "tiny_swarm_world.infrastructure.adapters.clients.lxc.images.lxc_container_image_publisher",
        )
        self.assertEqual(
            composition.LxcNexusHttpClient.__module__,
            "tiny_swarm_world.infrastructure.adapters.clients.lxc.services.lxc_nexus_http_client",
        )
        self.assertEqual(
            composition.LxcPortainerAdminClient.__module__,
            "tiny_swarm_world.infrastructure.adapters.clients.lxc.services.lxc_portainer_admin_client",
        )
        self.assertEqual(
            composition.LxcPortainerHttpClient.__module__,
            "tiny_swarm_world.infrastructure.adapters.clients.lxc.services.lxc_portainer_http_client",
        )

    def test_legacy_module_exposes_only_approved_runtime_facades_as_classes(self):
        source_path = (
            Path(__file__).parents[2]
            / "src"
            / "tiny_swarm_world"
            / "infrastructure"
            / "adapters"
            / "clients"
            / "lxc_swarm_runtime.py"
        )
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        class_names = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
        }

        self.assertEqual(
            class_names,
            {
                "LxcSwarmRuntime",
                "LxcPortainerAdminClient",
                "LxcNexusHttpClient",
                "LxcPortainerHttpClient",
            },
        )

    def test_node_provider_legacy_module_keeps_command_types_as_compatibility_imports(self):
        source_path = (
            Path(__file__).parents[2]
            / "src"
            / "tiny_swarm_world"
            / "infrastructure"
            / "adapters"
            / "clients"
            / "lxc_node_provider.py"
        )
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        class_names = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
        }

        self.assertNotIn("LxcNodeCommandResult", class_names)
        self.assertNotIn("AsyncLxcNodeCommandRunner", class_names)
        self.assertIn("LxcNodeProvider", class_names)
