import ast
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src" / "tiny_swarm_world"
DOMAIN_ROOT = SOURCE_ROOT / "domain"
APPLICATION_ROOT = SOURCE_ROOT / "application"
PACKAGE_NAME = "tiny_swarm_world"


class TestHexagonalImports(unittest.TestCase):
    def test_domain_has_no_infrastructure_imports(self):
        violations = _find_forbidden_imports(
            root=DOMAIN_ROOT,
            forbidden_prefix="tiny_swarm_world.infrastructure",
        )

        self.assertEqual([], violations)

    def test_domain_has_no_application_imports(self):
        violations = _find_forbidden_imports(
            root=DOMAIN_ROOT,
            forbidden_prefix="tiny_swarm_world.application",
        )

        self.assertEqual([], violations)

    def test_application_has_no_infrastructure_imports(self):
        violations = _find_forbidden_imports(
            root=APPLICATION_ROOT,
            forbidden_prefix="tiny_swarm_world.infrastructure",
        )

        self.assertEqual([], violations)


def _find_forbidden_imports(
    root: Path,
    forbidden_prefix: str,
) -> list[tuple[str, str, int]]:
    violations = []
    for source_file in sorted(root.rglob("*.py")):
        importer = _module_name(source_file)
        for imported, line_number in _direct_imports(source_file):
            if not _is_forbidden_import(imported, forbidden_prefix):
                continue
            violations.append((importer, imported, line_number))
    return violations


def _module_name(source_file: Path) -> str:
    return ".".join((PACKAGE_NAME, *source_file.with_suffix("").relative_to(SOURCE_ROOT).parts))


def _direct_imports(source_file: Path) -> list[tuple[str, int]]:
    tree = ast.parse(source_file.read_text(encoding="utf-8"))
    imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((alias.name, node.lineno) for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append((node.module, node.lineno))
    return imports


def _is_forbidden_import(imported: str, forbidden_prefix: str) -> bool:
    return imported == forbidden_prefix or imported.startswith(f"{forbidden_prefix}.")
