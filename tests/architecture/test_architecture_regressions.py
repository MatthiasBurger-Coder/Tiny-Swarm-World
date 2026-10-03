"""Mutation-tested architecture rules for the documented Python boundaries."""

import ast
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


PACKAGE = "tiny_swarm_world"
SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src" / PACKAGE
ROOT_ENTRYPOINTS = {
    "__main__": frozenset({"tiny_swarm_world.infrastructure.adapters.cli.dispatcher"}),
    "installer": frozenset({"tiny_swarm_world.infrastructure.composition_installation"}),
    "simple_installer": frozenset({"tiny_swarm_world.infrastructure.composition_installation"}),
    "prepare_linux": frozenset({
        "tiny_swarm_world.infrastructure.composition_native_preparation",
        "tiny_swarm_world.infrastructure.composition_installation",
    }),
}
# Explicit outward compatibility exports; infrastructure never imports this facade.
LEGACY_ROOT_IMPORTS = {
    "cli_presentation": frozenset({
        "tiny_swarm_world.infrastructure.adapters.cli.presentation",
    }),
}
CLI_MODULES = frozenset({
    "tiny_swarm_world.__main__",
    "tiny_swarm_world.installer",
    "tiny_swarm_world.simple_installer",
    "tiny_swarm_world.prepare_linux",
    "tiny_swarm_world.cli_presentation",
})
ALLOWED_ROOT_MODULES = frozenset().union(
    *ROOT_ENTRYPOINTS.values(), *LEGACY_ROOT_IMPORTS.values()
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
            elif _matches(module, PACKAGE + ".infrastructure.adapters.cli") and _matches(
                imported, PACKAGE + ".infrastructure"
            ) and not any(_matches(imported, prefix) for prefix in (
                PACKAGE + ".infrastructure.adapters.cli",
                PACKAGE + ".infrastructure.composition",
            )):
                rule = "CLI adapters must resolve runtime dependencies through composition"
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
                ) and imported not in ROOT_ENTRYPOINTS[root_name]:
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


THIN_BOOTSTRAPS = frozenset({
    "__main__.py", "installer.py", "simple_installer.py", "cli_presentation.py",
})
INSTALLATION_TECHNOLOGY = frozenset({
    "os", "sys", "subprocess", "shutil", "shlex", "tempfile", "stat", "socket",
    "requests", "yaml", "ruamel",
})
STATE_METHODS = frozenset({
    "open", "read_text", "read_bytes", "write_text", "write_bytes", "mkdir", "unlink",
    "chmod", "stat", "lstat", "exists", "is_file", "is_dir", "glob", "rglob",
    "iterdir", "rename", "touch", "rmdir",
})


def _direct_state_access(tree: ast.AST) -> list[ast.Call]:
    return [
        node for node in ast.walk(tree) if isinstance(node, ast.Call) and (
            isinstance(node.func, ast.Attribute) and node.func.attr in STATE_METHODS
            or isinstance(node.func, ast.Attribute) and node.func.attr in {"replace", "resolve"}
            and isinstance(node.func.value, ast.Call)
            and isinstance(node.func.value.func, ast.Name) and node.func.value.func.id == "Path"
            or isinstance(node.func, ast.Name) and node.func.id in {"open", "input"}
        )
    ]


def _bootstrap_logic(tree: ast.Module) -> list[ast.AST]:
    findings: list[ast.AST] = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue
        if isinstance(node, ast.Assign) and all(
            isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
        ) and isinstance(node.value, (ast.List, ast.Tuple)):
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in {"main", "cli", "run"}:
            body = [item for item in node.body if not (
                isinstance(item, (ast.Import, ast.ImportFrom))
                or isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant)
            )]
            if len(body) == 1 and isinstance(body[0], (ast.Expr, ast.Return)):
                call = body[0].value
                if isinstance(call, ast.Await):
                    call = call.value
                if isinstance(call, ast.Call):
                    continue
        if isinstance(node, ast.If) and ast.dump(node.test) == ast.dump(ast.parse(
            "__name__ == '__main__'", mode="eval"
        ).body) and not node.orelse:
            if len(node.body) == 1 and isinstance(node.body[0], (ast.Expr, ast.Raise)):
                continue
        findings.append(node)
    return findings


def _bootstrap_calls(tree: ast.Module) -> list[ast.Call]:
    """Entrypoints call delegates; constructors and I/O belong to their named owners."""
    allowed = {
        "main", "cli", "run", "_main", "_cli", "_run", "SystemExit",
        "build_installation_service", "simple_install_main",
    }
    findings = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = node.func.id if isinstance(node.func, ast.Name) else (
            node.func.attr if isinstance(node.func, ast.Attribute) else None
        )
        if name not in allowed:
            findings.append(node)
    return findings


def orchestration_edge_violations(source_root: Path) -> list[str]:
    """Protect executable delegation and the extracted installer/renderer responsibilities."""
    findings: list[str] = []
    for path in sorted(source_root.rglob("*.py")):
        relative = path.relative_to(source_root).as_posix()
        thin = relative in THIN_BOOTSTRAPS
        installation = relative.startswith("application/services/installation")
        rendering = relative == "infrastructure/adapters/cli/presentation.py"
        if not (thin or installation or rendering):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        for state_call in _direct_state_access(tree):
            findings.append(f"{relative}:{state_call.lineno}: technology/state access belongs in an adapter")
        for node in ast.walk(tree):
            imported: list[str] = []
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported = [node.module or ""]
            forbidden = INSTALLATION_TECHNOLOGY - ({"os", "sys"} if rendering else set())
            if any(name.split(".")[0] in forbidden for name in imported):
                findings.append(f"{relative}:{getattr(node, 'lineno', 0)}: technology import belongs in an adapter")
            renderer_dtos = {
                PACKAGE + ".application.services.artifacts.ArtifactWorkflowResult",
                PACKAGE + ".application.services.deployment.DeploymentWorkflowResult",
                PACKAGE + ".application.services.platform.workflow.results.PlatformWorkflowResult",
                PACKAGE + ".application.services.setup.SetupWorkflowResult",
                PACKAGE + ".application.services.setup.installation_plan.SetupInstallationPlan",
            }
            if rendering and any(
                _matches(name, PACKAGE + ".infrastructure")
                or _matches(name, PACKAGE + ".application.services") and name not in renderer_dtos
                for name, _line in _imports(
                    node, PACKAGE + ".infrastructure.adapters.cli.presentation", False, source_root,
                )
            ):
                findings.append(f"{relative}:{getattr(node, 'lineno', 0)}: renderer must not construct or execute workflows")
            if installation and isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == "print":
                    findings.append(f"{relative}:{node.lineno}: presentation belongs behind the installation port")
        if thin:
            findings.extend(
                f"{relative}:{getattr(node, 'lineno', 0)}: root bootstrap must only delegate; move orchestration to its owner"
                for node in _bootstrap_logic(tree)
            )
            findings.extend(
                f"{relative}:{node.lineno}: root bootstrap may call only its execution delegate"
                for node in _bootstrap_calls(tree)
            )
    return sorted(set(findings))


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
            ("installer.py", "from tiny_swarm_world.infrastructure.adapters import docker\n", "root entrypoint"),
            ("installer.py", "from tiny_swarm_world.infrastructure.adapters.host import *\n", "root entrypoint"),
            ("simple_installer.py", "from tiny_swarm_world.infrastructure import composition_runtime\n", "root entrypoint"),
            ("new_entrypoint.py", "from tiny_swarm_world.infrastructure.adapters import docker\n", "root module"),
            ("infrastructure/adapters/cli/commands.py",
             "from tiny_swarm_world.infrastructure.adapters.host import HostEnvironmentDetector\n",
             "CLI adapters must resolve"),
            ("infrastructure/adapters/cli/dispatcher.py",
             "from tiny_swarm_world import installer\n",
             "infrastructure may not"),
            ("installer.py",
             "from tiny_swarm_world.infrastructure.composition_installation import *\n",
             "root entrypoint"),
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
            ("__main__.py", "from tiny_swarm_world.infrastructure.adapters.cli import dispatcher\n"),
            ("infrastructure/composition.py", "from tiny_swarm_world.infrastructure.adapters import docker\n"),
            ("installer.py", "from tiny_swarm_world.infrastructure import composition_installation\n"),
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
                "installer.py:1: root entrypoint" in finding
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


class TestOrchestrationEdgeGuards(unittest.TestCase):
    def _findings(self, filename: str, source: str) -> list[str]:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding="utf-8")
            return orchestration_edge_violations(root)

    def test_root_bootstrap_rejects_workflow_logic_and_local_models(self):
        probes = (
            ("__main__.py", "async def main(argv=None):\n    if argv:\n        await dispatch(argv)\n"),
            ("installer.py", "def run(options):\n    for phase in options.phases:\n        execute(phase)\n"),
            ("simple_installer.py", "class InstallerOptions:\n    pass\n"),
            ("__main__.py", "def parse_args(argv):\n    return parser.parse_args(argv)\n"),
            ("installer.py", "def run(options):\n    command = build_command(options)\n    return execute(command)\n"),
        )
        for filename, source in probes:
            with self.subTest(filename=filename, source=source):
                self.assertTrue(self._findings(filename, source))

    def test_root_bootstrap_rejects_technology_and_module_alias_bypasses(self):
        probes = (
            "import os\n",
            "from subprocess import run as execute\n",
            "import sys\nsys.modules[__name__] = adapter\n",
            "from pathlib import Path\nPath('state').write_text('unsafe')\n",
            "def run(options):\n    return print(options)\n",
            "def run(options):\n    return __import__('os').system(options.command)\n",
        )
        for source in probes:
            with self.subTest(source=source):
                self.assertTrue(self._findings("installer.py", source))

    def test_installation_application_rejects_technology_and_direct_state_access(self):
        probes = (
            "import shutil\n",
            "import subprocess as process\n",
            "from os import environ\n",
            "def run(port):\n    port.path.write_text('unsafe')\n",
            "def run(port):\n    with open('state') as stream:\n        return stream.read()\n",
            "def run(port):\n    print('result')\n",
            "from pathlib import Path\ndef run(port):\n    Path('state').replace('target')\n",
        )
        for source in probes:
            with self.subTest(source=source):
                self.assertTrue(self._findings("application/services/installation.py", source))

    def test_cli_renderer_cannot_acquire_runtime_or_composition_responsibilities(self):
        probes = (
            "from tiny_swarm_world.infrastructure.composition import build_application_services\n",
            "from tiny_swarm_world.application.services.cli_dispatch import run_platform_action\n",
            "from pathlib import Path\nPath('state').read_text()\n",
            "from tiny_swarm_world.application.services.installation import InstallationService\ndef render(service):\n    return service.run()\n",
            "from tiny_swarm_world.application.services.setup import SetupService\n",
            "from tiny_swarm_world.application.services.setup import *\n",
            "from ....application.services.installation import InstallationService\n",
        )
        for source in probes:
            with self.subTest(source=source):
                self.assertTrue(self._findings("infrastructure/adapters/cli/presentation.py", source))

    def test_delegation_and_fake_port_orchestration_remain_allowed(self):
        probes = (
            ("__main__.py", "import asyncio\nasync def main(argv=None):\n    return await _main(argv)\ndef cli(argv=None):\n    asyncio.run(main(argv))\n"),
            ("installer.py", "from tiny_swarm_world.infrastructure.composition_installation import run\n"),
            ("application/services/installation.py", "def run(host, configuration, phases):\n    host.qualify()\n    with configuration.snapshot() as context:\n        return phases.setup(context)\n"),
            ("infrastructure/adapters/cli/presentation.py", "from tiny_swarm_world.application.services.setup import SetupWorkflowResult\n"),
            ("infrastructure/adapters/cli/presentation.py", "from ....application.services.setup import SetupWorkflowResult\n"),
            ("infrastructure/adapters/cli/presentation.py", "import json\ndef render(result):\n    print(json.dumps(result.to_dict()))\n"),
            ("infrastructure/adapters/cli/presentation.py", "def render(value):\n    return str(value).replace('\\n', ' ')\n"),
        )
        for filename, source in probes:
            with self.subTest(filename=filename):
                self.assertEqual([], self._findings(filename, source))

    def test_integrated_entrypoints_and_installation_respect_responsibilities(self):
        self.assertEqual([], orchestration_edge_violations(SOURCE_ROOT))


if __name__ == "__main__":
    unittest.main()
