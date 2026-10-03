"""Mutation-tested architecture rules for the documented Python boundaries."""

import ast
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


PACKAGE = "tiny_swarm_world"
SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src" / PACKAGE
ROOT_ENTRYPOINTS = {
    "__main__": "tiny_swarm_world.infrastructure.composition",
    "prepare_linux": "tiny_swarm_world.infrastructure.composition_native_preparation",
}
# ARCH-03.02 records the owner and migration rationale for these legacy edges.
# These are exact module names: a new submodule or sibling needs review.
LEGACY_ROOT_IMPORTS = {
    "installer": frozenset({
        "tiny_swarm_world.infrastructure.adapters.host",
        "tiny_swarm_world.infrastructure.adapters.ingress.tls_state",
        "tiny_swarm_world.infrastructure.adapters.preflight.windows_wsl_bridge_state",
        "tiny_swarm_world.infrastructure.adapters.repositories.installer_configuration_repository",
        "tiny_swarm_world.infrastructure.adapters.repositories.port_registry_yaml_repository",
        "tiny_swarm_world.infrastructure.adapters.repositories.project_filesystem_evidence_local_repository",
        "tiny_swarm_world.infrastructure.adapters.repositories.secret_manifest_yaml_repository",
        "tiny_swarm_world.infrastructure.adapters.ui.install_reporter",
        "tiny_swarm_world.infrastructure.composition_native_preparation",
        "tiny_swarm_world.infrastructure.process.runner",
        "tiny_swarm_world.infrastructure.process.streaming",
    }),
    "simple_installer": frozenset({
        "tiny_swarm_world.installer",
        "tiny_swarm_world.infrastructure.composition_operator_configuration",
    }),
}
CLI_MODULES = frozenset({
    "tiny_swarm_world.__main__",
    "tiny_swarm_world.installer",
    "tiny_swarm_world.simple_installer",
    "tiny_swarm_world.prepare_linux",
    "tiny_swarm_world.cli_presentation",
})
ALLOWED_ROOT_MODULES = frozenset(ROOT_ENTRYPOINTS.values()).union(
    *LEGACY_ROOT_IMPORTS.values()
)
# Existing compatibility cycles from ARCH-03.01, including the later network
# capability. A removal is welcome; a new cyclic edge requires architecture review.
REVIEWED_COMPOSITION_CYCLE_EDGES = frozenset({
    ("composition", "composition_runtime"),
    ("composition_runtime", "composition_artifacts"),
    ("composition_runtime", "composition_deployment"),
    ("composition_runtime", "composition_network"),
    ("composition_runtime", "composition_platform"),
    ("composition_runtime", "composition_setup"),
    ("composition_artifacts", "composition_runtime"),
    ("composition_deployment", "composition_runtime"),
    ("composition_network", "composition_runtime"),
    ("composition_platform", "composition_runtime"),
    ("composition_setup", "composition_runtime"),
    ("composition_setup", "composition"),
})


def _matches(imported: str, prefix: str) -> bool:
    return imported == prefix or imported.startswith(prefix + ".")


def _module_exists(source_root: Path, module: str) -> bool:
    parts = module.split(".")
    if parts[0] != PACKAGE:
        return False
    target = source_root.joinpath(*parts[1:])
    return target.with_suffix(".py").is_file() or (target / "__init__.py").is_file()


def _imports(
    tree: ast.AST, module: str, is_package: bool, source_root: Path,
) -> list[tuple[str, int]]:
    package = module if is_package else module.rpartition(".")[0]
    imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            parts = package.split(".")
            if node.level:
                parts = parts[:len(parts) - node.level + 1]
                base = ".".join((*parts, *((node.module or "").split("."))))
                base = base.rstrip(".")
            else:
                base = node.module or ""
            for alias in node.names:
                candidate = f"{base}.{alias.name}"
                if (
                    base in ALLOWED_ROOT_MODULES
                    and alias.name != "*"
                    and not _module_exists(source_root, candidate)
                ):
                    imports.append((base, node.lineno))
                else:
                    imports.append((candidate, node.lineno))
    return imports


def architecture_violations(source_root: Path) -> list[str]:
    """Return file, line, import and violated rule for each dependency edge."""
    violations = set()
    for path in sorted(source_root.rglob("*.py")):
        relative = path.relative_to(source_root)
        parts = relative.with_suffix("").parts
        module = ".".join((PACKAGE, *parts))
        is_package = parts[-1] == "__init__"
        if is_package:
            module = module.removesuffix(".__init__")
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for imported, line in _imports(tree, module, is_package, source_root):
            rule = None
            if _matches(module, PACKAGE + ".domain") and any(
                _matches(imported, PACKAGE + "." + layer)
                for layer in ("application", "infrastructure", "interfaces")
            ):
                rule = "domain may not import application, infrastructure or interfaces"
            elif _matches(module, PACKAGE + ".application") and any(
                _matches(imported, prefix)
                for prefix in (PACKAGE + ".infrastructure", *CLI_MODULES)
            ):
                rule = "application must use ports, not concrete runtime or CLI"
            elif _matches(module, PACKAGE + ".application.ports") and _matches(
                imported, PACKAGE + ".application.services"
            ):
                rule = "ports may not import application services"
            elif _matches(module, PACKAGE + ".infrastructure") and any(
                _matches(imported, cli) for cli in CLI_MODULES
            ):
                rule = "infrastructure may not import CLI or bootstrap"
            elif _matches(
                module, PACKAGE + ".infrastructure.adapters.clients.lxc.resource"
            ) and _matches(
                imported, PACKAGE + ".infrastructure.adapters.clients.lxc_node_provider"
            ):
                rule = "resource qualification may not depend on lifecycle provider"
            elif len(parts) == 1:
                root_name = parts[0]
                if root_name in ROOT_ENTRYPOINTS and _matches(
                    imported, PACKAGE + ".infrastructure"
                ) and not _matches(imported, ROOT_ENTRYPOINTS[root_name]):
                    rule = "root entrypoint must use its composition boundary"
                elif root_name in LEGACY_ROOT_IMPORTS and (
                    _matches(imported, PACKAGE + ".infrastructure")
                    or imported in CLI_MODULES
                ) and (
                    imported not in LEGACY_ROOT_IMPORTS[root_name]
                    or imported.endswith(".*")
                ):
                    rule = "legacy root import is outside the exact exception list"
                elif root_name not in (*ROOT_ENTRYPOINTS, *LEGACY_ROOT_IMPORTS) and _matches(
                    imported, PACKAGE + ".infrastructure"
                ):
                    rule = "root module must not bypass composition ownership"
            if rule:
                violations.add(f"{relative}:{line}: {rule}: {imported}")
    return sorted(violations)


def composition_cycle_edges(source_root: Path) -> set[tuple[str, str]]:
    """Find import edges on directed cycles between composition modules."""
    infrastructure = source_root / "infrastructure"
    modules = {path.stem: path for path in infrastructure.glob("composition*.py")}
    graph: dict[str, set[str]] = {name: set() for name in modules}
    for name, path in modules.items():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        module = f"{PACKAGE}.infrastructure.{name}"
        for imported, _line in _imports(tree, module, False, source_root):
            target = imported.removeprefix(f"{PACKAGE}.infrastructure.").split(".")[0]
            if target in modules and target != name:
                graph[name].add(target)

    def reaches(start: str, goal: str) -> bool:
        pending = [start]
        seen = set()
        while pending:
            current = pending.pop()
            if current == goal:
                return True
            if current not in seen:
                seen.add(current)
                pending.extend(graph[current] - seen)
        return False

    return {(source, target) for source, targets in graph.items()
            for target in targets if reaches(target, source)}


class TestArchitectureRegressions(unittest.TestCase):
    def test_repository_respects_documented_boundaries(self):
        self.assertEqual([], architecture_violations(SOURCE_ROOT))

    def test_composition_cycles_do_not_gain_edges(self):
        added = composition_cycle_edges(SOURCE_ROOT) - REVIEWED_COMPOSITION_CYCLE_EDGES
        self.assertEqual(set(), added, f"new composition cycle edges: {sorted(added)}")

    def test_prohibited_dependency_mutations_fail_with_actionable_messages(self):
        cases = (
            ("domain/model.py", "from ..infrastructure.adapters import docker\n", "domain may not"),
            ("application/services/workflow.py", "from ...infrastructure import composition_runtime\n", "application must use ports"),
            ("application/services/workflow.py", "from tiny_swarm_world.infrastructure.adapters.host import HostAdapter\nHostAdapter()\n", "application must use ports"),
            ("application/ports/repository.py", "from ..services import setup\n", "ports may not"),
            ("application/services/workflow.py", "from tiny_swarm_world import installer\n", "application must use ports"),
            ("infrastructure/adapters/runner.py", "from tiny_swarm_world import cli_presentation\n", "infrastructure may not"),
            ("__main__.py", "from tiny_swarm_world.infrastructure.adapters import docker\n", "root entrypoint"),
            ("prepare_linux.py", "from tiny_swarm_world.infrastructure import composition_runtime\n", "root entrypoint"),
            ("installer.py", "from tiny_swarm_world.infrastructure.adapters import docker\n", "legacy root import"),
            ("installer.py", "from tiny_swarm_world.infrastructure.adapters.host import *\n", "legacy root import"),
            ("simple_installer.py", "from tiny_swarm_world.infrastructure import composition_runtime\n", "legacy root import"),
            ("new_entrypoint.py", "from tiny_swarm_world.infrastructure.adapters import docker\n", "root module"),
            ("infrastructure/adapters/clients/lxc/resource/qualification.py",
             "from tiny_swarm_world.infrastructure.adapters.clients.lxc_node_provider import LxcNodeProvider\n",
             "resource qualification may not"),
            ("infrastructure/adapters/clients/lxc/resource/qualification.py",
             "from ...lxc_node_provider import LxcNodeProvider\n",
             "resource qualification may not"),
        )
        for filename, source, rule in cases:
            with self.subTest(filename=filename, source=source), TemporaryDirectory() as directory:
                path = Path(directory) / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source, encoding="utf-8")
                findings = architecture_violations(Path(directory))
                self.assertTrue(any(filename + ":1:" in finding and rule in finding
                                    for finding in findings), findings)

    def test_composition_and_exact_legacy_imports_remain_allowed(self):
        cases = (
            ("__main__.py", "from tiny_swarm_world.infrastructure import composition\n"),
            ("infrastructure/composition.py", "from tiny_swarm_world.infrastructure.adapters import docker\n"),
            ("installer.py", "from tiny_swarm_world.infrastructure.process import runner\n"),
            ("application/services/setup.py", "from tiny_swarm_world.application.ports import runtime\n"),
        )
        for filename, source in cases:
            with self.subTest(filename=filename), TemporaryDirectory() as directory:
                path = Path(directory) / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source, encoding="utf-8")
                self.assertEqual([], architecture_violations(Path(directory)))

    def test_allowlisted_package_does_not_hide_a_child_adapter(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            child = root / "infrastructure/adapters/host/new_adapter.py"
            child.parent.mkdir(parents=True)
            child.write_text("class Adapter: pass\n", encoding="utf-8")
            installer = root / "installer.py"
            installer.write_text(
                "from tiny_swarm_world.infrastructure.adapters.host import new_adapter\n",
                encoding="utf-8",
            )
            self.assertTrue(any(
                "installer.py:1: legacy root import" in finding
                and finding.endswith("host.new_adapter")
                for finding in architecture_violations(root)
            ))

    def test_new_composition_cycle_is_detected(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            infrastructure = root / "infrastructure"
            infrastructure.mkdir()
            (infrastructure / "composition_alpha.py").write_text(
                "from . import composition_beta\n", encoding="utf-8",
            )
            (infrastructure / "composition_beta.py").write_text(
                "from .composition_alpha import build\n", encoding="utf-8",
            )
            self.assertEqual({
                ("composition_alpha", "composition_beta"),
                ("composition_beta", "composition_alpha"),
            }, composition_cycle_edges(root))


class TestPreflightBoundaryContract(unittest.IsolatedAsyncioTestCase):
    async def test_standard_missing_collaborators_block_real_pre_apply_guard(self):
        from tests.application.services.platform.test_preflight_service import _fake_probe
        from tiny_swarm_world.application.ports.preflight import PortPlatformPreflight
        from tiny_swarm_world.application.services.platform.preflight_service import PreflightService
        from tiny_swarm_world.application.services.platform.workflow.runtime import _pre_apply_guard_verification
        from tiny_swarm_world.domain.preflight.completeness import PreflightConstruction

        preflight: PortPlatformPreflight = PreflightService(
            _fake_probe(), construction=PreflightConstruction.STANDARD_SETUP,
        )
        result = await preflight.run()
        self.assertTrue(result.executed_checks_passed)
        self.assertFalse(result.qualified)
        verification = _pre_apply_guard_verification(result)
        self.assertIsNotNone(verification)
        self.assertEqual("blocked", verification.status.value)
        self.assertIn("PREFLIGHT-COLLABORATORS", {check.check_id for check in result.failed_checks})


if __name__ == "__main__":
    unittest.main()
