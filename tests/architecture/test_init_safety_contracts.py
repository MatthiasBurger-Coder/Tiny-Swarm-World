import ast
import unittest
from pathlib import Path

from ruamel.yaml import YAML


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOT = REPOSITORY_ROOT / "infra" / "config"
APPLICATION_SERVICES_ROOT = (
    REPOSITORY_ROOT / "src" / "tiny_swarm_world" / "application" / "services"
)

DESTRUCTIVE_COMMAND_PATTERNS = (
    "docker system prune",
    "docker volume rm",
    "docker stack rm",
)
DESTRUCTIVE_COMMAND_YAML_FILES: set[str] = set()
DESTRUCTIVE_WORKFLOWS = {"platform:reset", "platform:destroy"}


class TestInitSafetyContracts(unittest.TestCase):
    def test_destructive_command_yaml_files_are_identified_by_static_patterns(self):
        destructive_files = {
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for path in CONFIG_ROOT.rglob("command_*.yaml")
            if _contains_any(path.read_text(encoding="utf-8"), DESTRUCTIVE_COMMAND_PATTERNS)
        }

        self.assertEqual(DESTRUCTIVE_COMMAND_YAML_FILES, destructive_files)

    def test_destructive_patterns_are_classified_and_reset_destroy_only(self):
        violations = {}
        yaml = YAML()

        for path in CONFIG_ROOT.rglob("command_*.yaml"):
            catalog = yaml.load(path.read_text(encoding="utf-8")) or {}
            for command in catalog.get("commands", []):
                command_text = command.get("command", "")
                if not _contains_any(command_text, DESTRUCTIVE_COMMAND_PATTERNS):
                    continue
                allowed_workflows = set(command.get("allowed_workflows", []))
                if command.get("safety_class") != "destructive":
                    violations[command["id"]] = "missing destructive safety class"
                elif not allowed_workflows or allowed_workflows - DESTRUCTIVE_WORKFLOWS:
                    violations[command["id"]] = sorted(allowed_workflows)

        self.assertEqual({}, violations)

    def test_reconcile_application_services_do_not_reference_destructive_yaml(self):
        destructive_config_file_names = {
            Path(path).name for path in DESTRUCTIVE_COMMAND_YAML_FILES
        }
        violations = {}

        for source_file in _reconcile_service_files():
            selected_config_files = _run_async_config_file_literals(source_file)
            destructive_references = sorted(selected_config_files & destructive_config_file_names)
            if destructive_references:
                violations[source_file.relative_to(REPOSITORY_ROOT).as_posix()] = (
                    destructive_references
                )

        self.assertEqual({}, violations)


def _reconcile_service_files() -> list[Path]:
    return [
        path
        for path in APPLICATION_SERVICES_ROOT.rglob("*.py")
        if "reconcile" in path.relative_to(APPLICATION_SERVICES_ROOT).as_posix().lower()
    ]


def _run_async_config_file_literals(source_file: Path) -> set[str]:
    tree = ast.parse(source_file.read_text(encoding="utf-8"))
    config_files = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "run_async":
            continue
        if not node.args or not isinstance(node.args[0], ast.Constant):
            continue
        if isinstance(node.args[0].value, str):
            config_files.add(node.args[0].value)

    return config_files


def _contains_any(text: str, patterns: tuple[str, ...]) -> bool:
    normalized_text = text.lower()
    return any(pattern in normalized_text for pattern in patterns)


if __name__ == "__main__":
    unittest.main()
