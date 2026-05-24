import ast
import unittest
from pathlib import Path

from tiny_swarm_world.infrastructure.project_paths import logs_root


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_INVENTORY_ROOT = REPOSITORY_ROOT / "src" / "tiny_swarm_world" / "domain" / "inventory"
GITIGNORE = REPOSITORY_ROOT / ".gitignore"
FORBIDDEN_DOMAIN_IMPORTS = {
    "pathlib",
    "os",
    "subprocess",
    "requests",
    "yaml",
    "ruamel",
    "ruamel.yaml",
    "tiny_swarm_world.infrastructure",
    "tiny_swarm_world.application",
}


class TestLocalStateStorageArchitecture(unittest.TestCase):
    def test_local_state_root_is_gitignored(self):
        ignored_paths = GITIGNORE.read_text(encoding="utf-8").splitlines()

        self.assertIn("/.tiny-swarm-world/", ignored_paths)

    def test_runtime_logs_are_stored_under_local_state_root(self):
        log_path = str(logs_root()).replace("\\", "/")

        self.assertIn("/.tiny-swarm-world/logs", log_path)
        self.assertNotIn("/infra/logs", log_path)

    def test_domain_inventory_does_not_import_storage_or_adapter_details(self):
        violations: list[tuple[str, str, int]] = []
        for source_file in sorted(DOMAIN_INVENTORY_ROOT.rglob("*.py")):
            for imported, line_number in _direct_imports(source_file):
                if _is_forbidden_import(imported):
                    violations.append((str(source_file.relative_to(REPOSITORY_ROOT)), imported, line_number))

        self.assertEqual([], violations)

    def test_no_observed_state_configuration_is_committed_under_infra_config(self):
        config_root = REPOSITORY_ROOT / "infra" / "config"
        forbidden_names = {
            "observed_inventory.json",
            "observed_inventory.yaml",
            "verification_results.json",
        }
        committed_state_files = [
            path.relative_to(REPOSITORY_ROOT)
            for path in config_root.rglob("*")
            if path.name in forbidden_names
        ]

        self.assertEqual([], committed_state_files)


def _direct_imports(source_file: Path) -> list[tuple[str, int]]:
    tree = ast.parse(source_file.read_text(encoding="utf-8"))
    imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((alias.name, node.lineno) for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append((node.module, node.lineno))
    return imports


def _is_forbidden_import(imported: str) -> bool:
    return any(
        imported == forbidden or imported.startswith(f"{forbidden}.")
        for forbidden in FORBIDDEN_DOMAIN_IMPORTS
    )


if __name__ == "__main__":
    unittest.main()
