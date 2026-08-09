"""Enforce the Issue #188 production process-spawn boundary."""

from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src" / "tiny_swarm_world"
SPAWN_APIS = frozenset(
    {
        "subprocess.run",
        "subprocess.Popen",
        "subprocess.call",
        "subprocess.check_call",
        "subprocess.check_output",
        "subprocess.getstatusoutput",
        "asyncio.create_subprocess_exec",
        "asyncio.create_subprocess_shell",
        "os.system",
        "os.popen",
    }
)

# These are existing, separately governed process boundaries. New runtime
# adapters must use infrastructure.process instead of extending this map.
ALLOWED_DIRECT_PROCESS_BOUNDARIES = {
    "src/tiny_swarm_world/infrastructure/process/runner.py": {
        "subprocess.run",
    },
    "src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py": {
        "subprocess.run",
    },
    "src/tiny_swarm_world/infrastructure/adapters/clients/lxc_node_provider.py": {
        "asyncio.create_subprocess_exec",
    },
    "src/tiny_swarm_world/infrastructure/adapters/clients/lxc/services/common.py": {
        "subprocess.run",
    },
    "src/tiny_swarm_world/infrastructure/adapters/clients/lxc/services/lxc_portainer_http_client.py": {
        "subprocess.run",
    },
    "src/tiny_swarm_world/infrastructure/adapters/command_runner/async_command_runner.py": {
        "asyncio.create_subprocess_shell",
    },
    "src/tiny_swarm_world/infrastructure/adapters/preflight/artifact_readiness.py": {
        "subprocess.run",
    },
    "src/tiny_swarm_world/infrastructure/adapters/preflight/lxc_provider_preflight.py": {
        "asyncio.create_subprocess_exec",
    },
    "src/tiny_swarm_world/infrastructure/adapters/preflight/windows_wsl_bridge_state.py": {
        "subprocess.run",
    },
    "src/tiny_swarm_world/infrastructure/adapters/host/hang_diagnostics.py": {
        "subprocess.run",
    },
    "src/tiny_swarm_world/infrastructure/adapters/host/wsl_resource_inspector.py": {
        "subprocess.run",
    },
    "src/tiny_swarm_world/infrastructure/adapters/host/windows_command_runner.py": {
        "subprocess.Popen",
        "subprocess.run",
    },
    "src/tiny_swarm_world/infrastructure/adapters/network/host_network_probe.py": {
        "subprocess.run",
    },
    "src/tiny_swarm_world/infrastructure/adapters/network/host_network_repair.py": {
        "subprocess.run",
    },
    "src/tiny_swarm_world/infrastructure/adapters/ui/windows_ui.py": {
        "os.system",
    },
    "src/tiny_swarm_world/infrastructure/adapters/clients/infisical_cli_client.py": {
        "subprocess.run",
    },
    "src/tiny_swarm_world/infrastructure/composition.py": {
        "asyncio.create_subprocess_exec",
        "subprocess.run",
    },
    "src/tiny_swarm_world/installer.py": {
        "subprocess.Popen",
        "subprocess.run",
    },
}


class TestProcessSpawnBoundaries(unittest.TestCase):
    def test_required_process_api_families_are_covered(self):
        self.assertTrue(
            {
                "subprocess.run",
                "subprocess.Popen",
                "asyncio.create_subprocess_exec",
                "asyncio.create_subprocess_shell",
            }.issubset(SPAWN_APIS)
        )

    def test_existing_production_process_spawning_is_allowlisted(self):
        violations = _find_unallowlisted_process_spawns(REPOSITORY_ROOT)

        self.assertEqual([], violations)

    def test_new_unapproved_process_spawn_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository_root = Path(temporary_directory)
            source_file = (
                repository_root
                / "src"
                / "tiny_swarm_world"
                / "infrastructure"
                / "adapters"
                / "unapproved.py"
            )
            source_file.parent.mkdir(parents=True)
            source_file.write_text(
                "from subprocess import run\n\nrun(['unexpected'])\n",
                encoding="utf-8",
            )

            violations = _find_unallowlisted_process_spawns(repository_root)

        self.assertEqual(
            [("src/tiny_swarm_world/infrastructure/adapters/unapproved.py", 3, "subprocess.run")],
            violations,
        )


def _find_unallowlisted_process_spawns(repository_root: Path) -> list[tuple[str, int, str]]:
    source_root = repository_root / "src" / "tiny_swarm_world"
    findings: list[tuple[str, int, str]] = []
    for source_file in sorted(source_root.rglob("*.py")):
        relative_path = source_file.relative_to(repository_root).as_posix()
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        visitor = _ProcessSpawnVisitor()
        visitor.visit(tree)
        allowed = ALLOWED_DIRECT_PROCESS_BOUNDARIES.get(relative_path, set())
        findings.extend(
            (relative_path, line_number, api)
            for line_number, api in visitor.findings
            if api not in allowed
        )
    return sorted(findings)


class _ProcessSpawnVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.module_aliases: dict[str, str] = {}
        self.symbol_aliases: dict[str, str] = {}
        self.findings: list[tuple[int, str]] = []

    def visit_Import(self, node: ast.Import) -> None:
        for imported in node.names:
            if imported.name in {"subprocess", "asyncio", "os"}:
                self.module_aliases[imported.asname or imported.name] = imported.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module in {"subprocess", "asyncio", "os"}:
            for imported in node.names:
                canonical = f"{node.module}.{imported.name}"
                if canonical in SPAWN_APIS:
                    self.symbol_aliases[imported.asname or imported.name] = canonical
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        api = self._resolve(node)
        if api in SPAWN_APIS:
            self.findings.append((node.lineno, api))
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        api = self.symbol_aliases.get(node.id)
        if api in SPAWN_APIS:
            self.findings.append((node.lineno, api))
        self.generic_visit(node)

    def _resolve(self, node: ast.Attribute) -> str | None:
        parts: list[str] = []
        current: ast.AST = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if not isinstance(current, ast.Name):
            return None
        module = self.module_aliases.get(current.id)
        if module is None:
            return None
        parts.append(module)
        return ".".join(reversed(parts))


if __name__ == "__main__":
    unittest.main()
