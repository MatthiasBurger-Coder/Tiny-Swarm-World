import ast
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "docker"
DOMAIN_ROOT = SOURCE_ROOT / "domain"

LEGACY_DOMAIN_INFRASTRUCTURE_IMPORTS = {
    (
        "domain.command.command_builder.vm_parameter.command_builder",
        "infrastructure.adapters.command_runner.command_runner_factory",
    ),
    (
        "domain.command.command_builder.vm_parameter.command_builder",
        "infrastructure.adapters.repositories.vm_repository_yaml",
    ),
    (
        "domain.command.command_builder.vm_parameter.strategies.manager_strategy",
        "infrastructure.adapters.repositories.vm_repository_yaml",
    ),
    (
        "domain.command.command_builder.vm_parameter.strategies.manager_strategy",
        "infrastructure.logging.logger_factory",
    ),
    (
        "domain.command.command_builder.vm_parameter.strategies.worker_strategy",
        "infrastructure.adapters.repositories.vm_repository_yaml",
    ),
    (
        "domain.command.command_executer.command_executer",
        "infrastructure.logging.logger_factory",
    ),
    (
        "domain.network.ip_extractor.ip_extractor_builder",
        "infrastructure.logging.logger_factory",
    ),
    (
        "domain.network.ip_extractor.strategies.IpExtractorSwarmNodeIpList",
        "infrastructure.logging.logger_factory",
    ),
    (
        "domain.network.ip_extractor.strategies.ip_extractor_gateway",
        "infrastructure.logging.logger_factory",
    ),
    (
        "domain.network.ip_extractor.strategies.ip_extractor_swarm_manager",
        "infrastructure.logging.logger_factory",
    ),
}

LEGACY_DOMAIN_APPLICATION_IMPORTS = {
    (
        "domain.command.command_builder.vm_parameter.command_builder",
        "application.ports.repositories.port_command_repository",
    ),
    (
        "domain.command.command_builder.vm_parameter.strategies.command_builder_strategy",
        "application.ports.commands.port_command_runner_factory",
    ),
    (
        "domain.command.command_executer.command_executer",
        "application.ports.ui.port_ui",
    ),
    (
        "domain.command.command_executer.excecuteable_commands",
        "application.ports.commands.port_command_runner",
    ),
    (
        "domain.task.tasks",
        "application.ports.commands.port_command_runner",
    ),
}


class TestHexagonalImports(unittest.TestCase):
    def test_domain_has_no_new_infrastructure_imports(self):
        violations = _find_forbidden_domain_imports(
            forbidden_prefix="infrastructure",
            allowed_imports=LEGACY_DOMAIN_INFRASTRUCTURE_IMPORTS,
        )

        self.assertEqual([], violations)

    def test_domain_has_no_new_application_imports(self):
        violations = _find_forbidden_domain_imports(
            forbidden_prefix="application",
            allowed_imports=LEGACY_DOMAIN_APPLICATION_IMPORTS,
        )

        self.assertEqual([], violations)


def _find_forbidden_domain_imports(
    forbidden_prefix: str,
    allowed_imports: set[tuple[str, str]],
) -> list[tuple[str, str, int]]:
    violations = []
    for source_file in sorted(DOMAIN_ROOT.rglob("*.py")):
        importer = _module_name(source_file)
        for imported, line_number in _direct_imports(source_file):
            if not _is_forbidden_import(imported, forbidden_prefix):
                continue
            if (importer, imported) not in allowed_imports:
                violations.append((importer, imported, line_number))
    return violations


def _module_name(source_file: Path) -> str:
    return ".".join(source_file.with_suffix("").relative_to(SOURCE_ROOT).parts)


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
