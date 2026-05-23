import ast
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from tiny_swarm_world import __main__ as entrypoint


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT_PATH = REPOSITORY_ROOT / "src" / "tiny_swarm_world" / "__main__.py"


class TestPackageEntrypoint(unittest.IsolatedAsyncioTestCase):
    async def test_default_entrypoint_does_not_build_or_run_services(self):
        output = io.StringIO()

        with patch.object(entrypoint, "build_application_services") as build_services:
            with redirect_stdout(output):
                await entrypoint.main([])

        build_services.assert_not_called()
        self.assertIn("No automation service selected", output.getvalue())

    async def test_list_services_does_not_build_or_run_services(self):
        output = io.StringIO()

        with patch.object(entrypoint, "build_application_services") as build_services:
            with redirect_stdout(output):
                await entrypoint.main(["--list-services"])

        build_services.assert_not_called()
        self.assertIn("vm-ip-list", output.getvalue())
        self.assertIn("multipass-init-vms", output.getvalue())

    async def test_explicit_service_selection_runs_selected_service(self):
        vm_ip_list = SimpleNamespace(run=AsyncMock())
        services = SimpleNamespace(vm_ip_list=vm_ip_list)
        output = io.StringIO()

        with patch.object(entrypoint, "build_application_services", return_value=services):
            with redirect_stdout(output):
                await entrypoint.main(["--run", "vm-ip-list"])

        vm_ip_list.run.assert_awaited_once_with()
        self.assertIn("Done", output.getvalue())

    def test_entrypoint_has_no_direct_low_level_infrastructure_imports(self):
        imports = _direct_imports(ENTRYPOINT_PATH)
        forbidden_prefixes = (
            "tiny_swarm_world.infrastructure.adapters.command_runner",
            "tiny_swarm_world.infrastructure.adapters.repositories",
            "tiny_swarm_world.infrastructure.adapters.yaml",
            "tiny_swarm_world.infrastructure.adapters.file_management",
            "tiny_swarm_world.application.services.multipass",
            "tiny_swarm_world.application.services.network",
            "tiny_swarm_world.application.services.vm",
        )

        violations = [
            imported
            for imported in imports
            for prefix in forbidden_prefixes
            if imported == prefix or imported.startswith(f"{prefix}.")
        ]

        self.assertEqual([], violations)


def _direct_imports(source_file: Path) -> list[str]:
    tree = ast.parse(source_file.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports
