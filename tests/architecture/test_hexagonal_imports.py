import ast
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src" / "tiny_swarm_world"
DOMAIN_ROOT = SOURCE_ROOT / "domain"
PACKAGE_NAME = "tiny_swarm_world"

LEGACY_DOMAIN_INFRASTRUCTURE_IMPORTS = {
    (
        "tiny_swarm_world.domain.command.command_builder.vm_parameter.command_builder",
        "tiny_swarm_world.infrastructure.adapters.command_runner.command_runner_factory",
    ),
    (
        "tiny_swarm_world.domain.command.command_builder.vm_parameter.command_builder",
        "tiny_swarm_world.infrastructure.adapters.repositories.vm_repository_yaml",
    ),
    (
        "tiny_swarm_world.domain.command.command_builder.vm_parameter.strategies.manager_strategy",
        "tiny_swarm_world.infrastructure.adapters.repositories.vm_repository_yaml",
    ),
    (
        "tiny_swarm_world.domain.command.command_builder.vm_parameter.strategies.manager_strategy",
        "tiny_swarm_world.infrastructure.logging.logger_factory",
    ),
    (
        "tiny_swarm_world.domain.command.command_builder.vm_parameter.strategies.worker_strategy",
        "tiny_swarm_world.infrastructure.adapters.repositories.vm_repository_yaml",
    ),
    (
        "tiny_swarm_world.domain.command.command_executer.command_executer",
        "tiny_swarm_world.infrastructure.logging.logger_factory",
    ),
    (
        "tiny_swarm_world.domain.network.ip_extractor.ip_extractor_builder",
        "tiny_swarm_world.infrastructure.logging.logger_factory",
    ),
    (
        "tiny_swarm_world.domain.network.ip_extractor.strategies.IpExtractorSwarmNodeIpList",
        "tiny_swarm_world.infrastructure.logging.logger_factory",
    ),
    (
        "tiny_swarm_world.domain.network.ip_extractor.strategies.ip_extractor_gateway",
        "tiny_swarm_world.infrastructure.logging.logger_factory",
    ),
    (
        "tiny_swarm_world.domain.network.ip_extractor.strategies.ip_extractor_swarm_manager",
        "tiny_swarm_world.infrastructure.logging.logger_factory",
    ),
}

LEGACY_DOMAIN_APPLICATION_IMPORTS = {
    (
        "tiny_swarm_world.domain.command.command_builder.vm_parameter.command_builder",
        "tiny_swarm_world.application.ports.repositories.port_command_repository",
    ),
    (
        "tiny_swarm_world.domain.command.command_builder.vm_parameter.strategies.command_builder_strategy",
        "tiny_swarm_world.application.ports.commands.port_command_runner_factory",
    ),
    (
        "tiny_swarm_world.domain.command.command_executer.command_executer",
        "tiny_swarm_world.application.ports.ui.port_ui",
    ),
    (
        "tiny_swarm_world.domain.command.command_executer.excecuteable_commands",
        "tiny_swarm_world.application.ports.commands.port_command_runner",
    ),
    (
        "tiny_swarm_world.domain.task.tasks",
        "tiny_swarm_world.application.ports.commands.port_command_runner",
    ),
}


class TestHexagonalImports(unittest.TestCase):
    def test_domain_has_no_new_infrastructure_imports(self):
        violations = _find_forbidden_domain_imports(
            forbidden_prefix="tiny_swarm_world.infrastructure",
            allowed_imports=LEGACY_DOMAIN_INFRASTRUCTURE_IMPORTS,
        )

        self.assertEqual([], violations)

    def test_domain_has_no_new_application_imports(self):
        violations = _find_forbidden_domain_imports(
            forbidden_prefix="tiny_swarm_world.application",
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
