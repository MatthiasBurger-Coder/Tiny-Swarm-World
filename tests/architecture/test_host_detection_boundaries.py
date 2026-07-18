import ast
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src" / "tiny_swarm_world"


class TestHostDetectionBoundaries(unittest.TestCase):
    def test_domain_host_model_has_no_host_io_or_outward_imports(self):
        imports = {
            imported
            for path in (
                SOURCE_ROOT / "domain" / "host_environment.py",
                SOURCE_ROOT / "domain" / "project_filesystem.py",
            )
            for imported in _imports(path)
        }

        forbidden = {
            "os",
            "pathlib",
            "platform",
            "subprocess",
            "tiny_swarm_world.application",
            "tiny_swarm_world.infrastructure",
        }
        self.assertFalse(_matches_any(imports, forbidden), sorted(imports))

    def test_project_filesystem_evidence_port_has_no_adapter_or_file_io_imports(self):
        imports = _imports(
            SOURCE_ROOT
            / "application"
            / "ports"
            / "repositories"
            / "port_project_filesystem_evidence_repository.py"
        )

        forbidden = {
            "os",
            "pathlib",
            "tempfile",
            "tiny_swarm_world.infrastructure",
        }
        self.assertFalse(_matches_any(imports, forbidden), sorted(imports))

    def test_application_host_boundary_has_no_concrete_adapter_or_host_io_imports(self):
        roots = (
            SOURCE_ROOT / "application" / "ports" / "host",
            SOURCE_ROOT / "application" / "services" / "platform" / "host",
        )
        imports = {
            imported
            for root in roots
            for path in root.rglob("*.py")
            for imported in _imports(path)
        }

        forbidden = {
            "os",
            "pathlib",
            "platform",
            "subprocess",
            "tiny_swarm_world.infrastructure",
        }
        self.assertFalse(_matches_any(imports, forbidden), sorted(imports))

    def test_entrypoint_imports_composition_not_concrete_host_adapter(self):
        imports = _imports(SOURCE_ROOT / "__main__.py")

        self.assertNotIn(
            "tiny_swarm_world.infrastructure.adapters.host",
            imports,
        )

    def test_legacy_consumers_contain_no_independent_wsl_classifier(self):
        sources = {
            "preflight": (
                SOURCE_ROOT
                / "infrastructure"
                / "adapters"
                / "preflight"
                / "host_preflight_probe.py"
            ).read_text(encoding="utf-8"),
            "network": (
                SOURCE_ROOT
                / "infrastructure"
                / "adapters"
                / "network"
                / "host_network_probe.py"
            ).read_text(encoding="utf-8"),
            "os_types": (
                SOURCE_ROOT / "infrastructure" / "os_types.py"
            ).read_text(encoding="utf-8"),
        }

        self.assertNotIn("_wsl_environment_report", sources["preflight"])
        self.assertNotIn("grep -Eqi '(microsoft|wsl)'", sources["network"])
        self.assertNotIn("/proc/sys/kernel/osrelease", sources["os_types"])


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    return imported


def _matches_any(imports: set[str], prefixes: set[str]) -> bool:
    return any(
        imported == prefix or imported.startswith(prefix + ".")
        for imported in imports
        for prefix in prefixes
    )
