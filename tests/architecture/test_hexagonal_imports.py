import ast
import asyncio
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
import json
import sys
from types import SimpleNamespace, TracebackType

from pydantic import BaseModel
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src" / "tiny_swarm_world"
DOMAIN_ROOT = SOURCE_ROOT / "domain"
APPLICATION_ROOT = SOURCE_ROOT / "application"
APPLICATION_PORTS_ROOT = APPLICATION_ROOT / "ports"
APPLICATION_SERVICES_ROOT = APPLICATION_ROOT / "services"
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
PACKAGE_NAME = "tiny_swarm_world"
TARGET_RESPONSIBILITY_BOUNDARIES = ("platform", "artifacts", "deployment", "shared")
PLATFORM_APPLICATION_SERVICE_ROOTS = (
    APPLICATION_SERVICES_ROOT / "network",
    APPLICATION_SERVICES_ROOT / "platform",
)
DEPLOYMENT_APPLICATION_SERVICE_ROOTS = (
    APPLICATION_SERVICES_ROOT / "deployment",
)
ARTIFACT_APPLICATION_SERVICE_ROOTS = (
    APPLICATION_SERVICES_ROOT / "artifacts",
)
CONSOLE_UI_INFRASTRUCTURE_ROOT = SOURCE_ROOT / "infrastructure" / "adapters" / "ui"
CLI_ENTRYPOINT = SOURCE_ROOT / "__main__.py"
ALLOWED_APPLICATION_SERVICE_DIRECTORIES = {
    "commands",
    "configuration",
    "network",
    "nexus",
    "setup",
    *TARGET_RESPONSIBILITY_BOUNDARIES,
}
REQUIRED_ARCHITECTURE_DOCUMENTS = {
    "responsibility-separation-analysis.md": (
        DOCUMENTATION_ROOT / "arc42" / "05_analysis" / "responsibility-separation-analysis.md"
    ),
    "adr-separate-platform-artifacts-deployment.adoc": (
        DOCUMENTATION_ROOT / "arc42" / "09_decisions" / "adr-separate-platform-artifacts-deployment.adoc"
    ),
    "migration-plan.md": DOCUMENTATION_ROOT / "arc42" / "11_migration" / "migration-plan.md",
    "agent-split-plan.md": DOCUMENTATION_ROOT / "process" / "agent-plans" / "agent-split-plan.md",
}
KNOWN_MIXED_BOUNDARY_FILES = (
    "src/tiny_swarm_world/application/services/nexus/bootstrap_nexus.py",
    "src/tiny_swarm_world/infrastructure/composition.py",
)
ROOT_BOUNDARY_EXCEPTION_IMPORTS = {
    "src/tiny_swarm_world/cli_presentation.py": {
        "tiny_swarm_world.infrastructure.adapters.cli.presentation",
    },
}
ROOT_ENTRYPOINTS = {
    "src/tiny_swarm_world/prepare_incus.py": {
        "tiny_swarm_world.infrastructure.composition_native_preparation",
    },
    "src/tiny_swarm_world/__main__.py": {
        "tiny_swarm_world.infrastructure.adapters.cli.dispatcher",
    },
    "src/tiny_swarm_world/installer.py": {
        "tiny_swarm_world.infrastructure.composition_installation",
    },
    "src/tiny_swarm_world/simple_installer.py": {
        "tiny_swarm_world.infrastructure.composition_installation",
    },
    "src/tiny_swarm_world/prepare_linux.py": {
        "tiny_swarm_world.infrastructure.composition_native_preparation",
        "tiny_swarm_world.infrastructure.composition_installation",
    },
}
CLI_MODULES = (
    "tiny_swarm_world.__main__",
    "tiny_swarm_world.installer",
    "tiny_swarm_world.simple_installer",
)
FORBIDDEN_APPLICATION_TECHNOLOGY_IMPORTS = ("os", "yaml", "subprocess")
FORBIDDEN_CORE_PARSER_IMPORTS = ("yaml", "ruamel")
DIRECT_FILESYSTEM_METHODS = {
    "chmod",
    "exists",
    "glob",
    "is_file",
    "iterdir",
    "mkdir",
    "read_text",
    "rglob",
    "unlink",
    "write_text",
}


class TestHexagonalImports(unittest.TestCase):
    def test_operation_contract_depends_only_on_standard_library(self):
        source = (APPLICATION_PORTS_ROOT / "operation_result.py").read_text(encoding="utf-8")
        self.assertEqual([], _non_stdlib_imports(source))

    def test_operation_contract_import_probe_rejects_hidden_dependencies(self):
        for source in (
            "from tiny_swarm_world.application.services import setup",
            "def run():\n    import requests as http",
            "from . import operation_result",
            "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    import tiny_swarm_world.infrastructure",
        ):
            with self.subTest(source=source):
                self.assertTrue(_non_stdlib_imports(source))
        self.assertEqual([], _non_stdlib_imports("from dataclasses import dataclass\nimport enum"))

    def test_actual_operation_boundaries_contain_no_raw_failures(self):
        from tiny_swarm_world.application.ports.operation_result import OperationError, OperationFailure
        from tiny_swarm_world.application.services.deployment.workflows import DeploymentApplyWorkflow
        from tiny_swarm_world.application.services.setup.workflow import SetupWorkflow, SetupWorkflowPhase
        from tiny_swarm_world.domain.inventory import VerificationResult, VerificationStatus
        from tiny_swarm_world.domain.preflight import LiveConsent

        sentinel = "private-boundary-value-4827"
        typed = OperationError(OperationFailure.for_cause("service.request", "portainer", "request_failed"))
        typed.private_detail = sentinel

        async def exercise(error):
            def fail():
                raise error
            step = SimpleNamespace(
                run=fail,
                verify=lambda: VerificationResult("deployment:probe", VerificationStatus.VERIFIED, "Ready"),
            )
            deployment = DeploymentApplyWorkflow((step,))
            setup = SetupWorkflow(
                (SetupWorkflowPhase("deployment", deployment.run),),
                live_consent=LiveConsent(live_flag=True, confirmed=True),
            )
            return await setup.run()

        for error, cause in ((typed, "request_failed"), (RuntimeError(sentinel), "unexpected_failure")):
            with self.subTest(cause=cause), self.assertLogs("DeploymentApplyWorkflow", level="ERROR"):
                result = asyncio.run(exercise(error))
                self.assertEqual(cause, result.operation_result.failures[0].cause)
                self.assertEqual([], _find_unsafe_operation_objects(result))
                self.assertNotIn(sentinel, json.dumps(result.to_dict()))

    def test_operation_boundary_probe_detects_nested_exception_and_traceback(self):
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Boundary:
            value: object

        try:
            raise RuntimeError("private")
        except RuntimeError as error:
            value = Boundary({"nested": ([error, error.__traceback__],)})
            self.assertEqual(["RuntimeError", "traceback"], _find_unsafe_operation_objects(value))
        self.assertEqual([], _find_unsafe_operation_objects(Boundary({"safe": ("text", 1)})))

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

    def test_application_ports_do_not_import_application_services(self):
        violations = _find_forbidden_imports(
            root=APPLICATION_PORTS_ROOT,
            forbidden_prefix="tiny_swarm_world.application.services",
        )

        self.assertEqual([], violations)

    def test_application_services_access_local_state_only_through_ports(self):
        technology_imports = [
            violation
            for forbidden_prefix in FORBIDDEN_APPLICATION_TECHNOLOGY_IMPORTS
            for violation in _find_forbidden_imports(
                root=APPLICATION_SERVICES_ROOT,
                forbidden_prefix=forbidden_prefix,
            )
        ]
        filesystem_calls = _find_direct_filesystem_calls(APPLICATION_SERVICES_ROOT)

        self.assertEqual(technology_imports, [])
        self.assertEqual(filesystem_calls, [])

    def test_domain_and_entire_application_have_no_yaml_parser_imports(self):
        for root in (DOMAIN_ROOT, APPLICATION_ROOT):
            for prefix in FORBIDDEN_CORE_PARSER_IMPORTS:
                with self.subTest(layer=root.name, parser=prefix):
                    self.assertEqual([], _find_forbidden_imports(root, prefix))

    def test_yaml_parser_import_probes_cover_aliases_and_nested_scopes(self):
        probes = (
            "import ruamel",
            "import ruamel.yaml as parser",
            "from ruamel import yaml as parser",
            "from ruamel.yaml import YAML",
            "from ruamel.yaml.comments import CommentedMap",
            "import yaml as parser",
            "from yaml import safe_load",
            "def parse():\n    from ruamel.yaml import YAML as Parser",
            "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    import ruamel.yaml",
        )
        for source in probes:
            with self.subTest(source=source):
                self.assertTrue(any(
                    _is_forbidden_import(imported, prefix)
                    for imported in _direct_imports_from_source(source)
                    for prefix in FORBIDDEN_CORE_PARSER_IMPORTS
                ))
        for source in ("import ruamel_tools", "from yaml_helpers import parse", "import typing"):
            with self.subTest(allowed=source):
                self.assertFalse(any(
                    _is_forbidden_import(imported, prefix)
                    for imported in _direct_imports_from_source(source)
                    for prefix in FORBIDDEN_CORE_PARSER_IMPORTS
                ))

    def test_actual_configuration_results_contain_no_nested_parser_objects(self):
        from tiny_swarm_world.domain.configuration.secret_manifest import SecretManifestEntry
        from tiny_swarm_world.domain.deployment.stack_definition import StackConfigurationSnapshot
        from tiny_swarm_world.domain.inventory import DesiredInventory
        from tiny_swarm_world.domain.network import PortRegistry
        from tiny_swarm_world.infrastructure.adapters.repositories.compose_file_repository_yaml import ComposeFileRepositoryYaml
        from tiny_swarm_world.infrastructure.adapters.repositories.desired_inventory_yaml_repository import DesiredInventoryYamlRepository
        from tiny_swarm_world.infrastructure.adapters.repositories.node_provider_config_yaml_repository import NodeProviderConfig, NodeProviderConfigYamlRepository
        from tiny_swarm_world.infrastructure.adapters.repositories.port_registry_yaml_repository import PortRegistryYamlRepository
        from tiny_swarm_world.infrastructure.adapters.repositories.secret_manifest_yaml_repository import SecretManifestYamlRepository

        config = REPOSITORY_ROOT / "infra" / "config"
        inventory = DesiredInventoryYamlRepository(config / "inventory" / "desired_inventory.yaml").load()
        provider = NodeProviderConfigYamlRepository(config / "node-providers" / "provider_config.yaml").load()
        ports = PortRegistryYamlRepository(config / "ports.yaml").load()
        manifest = SecretManifestYamlRepository(config / "secrets" / "infisical-secrets.yaml").load()
        from tiny_swarm_world.infrastructure.project_paths import ProjectPaths

        compose = ComposeFileRepositoryYaml(
            project_paths=ProjectPaths.from_roots(REPOSITORY_ROOT), environment={},
        )
        snapshot = compose.validate_and_snapshot(("portainer",))
        self.assertIsInstance(inventory, DesiredInventory)
        self.assertIsInstance(provider, NodeProviderConfig)
        self.assertIsInstance(ports, PortRegistry)
        self.assertIsInstance(snapshot, StackConfigurationSnapshot)
        self.assertTrue(manifest)
        self.assertTrue(all(isinstance(entry, SecretManifestEntry) for entry in manifest))
        for result in (inventory, provider, ports, manifest, snapshot, compose.get_services_of("portainer")):
            with self.subTest(model=type(result).__name__):
                self.assertEqual([], _find_parser_objects(result))

    def test_recursive_boundary_probe_detects_parser_mapping_and_scalar(self):
        from dataclasses import dataclass
        from ruamel.yaml.comments import CommentedMap
        from ruamel.yaml.scalarstring import LiteralScalarString

        @dataclass(frozen=True)
        class SyntheticBoundary:
            nested: object

        for leaked in (CommentedMap({"value": "text"}), LiteralScalarString("text")):
            value = SyntheticBoundary({"levels": ([leaked],)})
            with self.subTest(parser_type=type(leaked).__name__):
                self.assertIn(type(leaked).__module__, _find_parser_objects(value))
        self.assertEqual([], _find_parser_objects(SyntheticBoundary({"levels": (["text"],)})))

    def test_application_does_not_import_cli_or_bootstrap_modules(self):
        violations = [
            violation
            for forbidden_prefix in CLI_MODULES
            for violation in _find_forbidden_imports(
                root=APPLICATION_ROOT,
                forbidden_prefix=forbidden_prefix,
            )
        ]

        self.assertEqual([], violations)

    def test_root_entrypoints_use_only_the_composition_boundary(self):
        from tests.architecture.test_architecture_regressions import _imports

        violations = []
        for relative_path, allowed_imports in ROOT_ENTRYPOINTS.items():
            source_file = REPOSITORY_ROOT / relative_path
            module = f"{PACKAGE_NAME}.{source_file.stem}"
            tree = ast.parse(source_file.read_text(encoding="utf-8"))
            for imported, line_number in _imports(tree, module, False, SOURCE_ROOT):
                if imported.startswith("tiny_swarm_world.infrastructure") and imported not in allowed_imports:
                    violations.append((relative_path, imported, line_number))

        self.assertEqual([], violations)

    def test_legacy_root_exceptions_are_explicit_and_traceable(self):
        for relative_path, allowed_imports in ROOT_BOUNDARY_EXCEPTION_IMPORTS.items():
            source_file = REPOSITORY_ROOT / relative_path
            observed = {
                imported
                for imported, _line_number in _direct_imports(source_file)
                if imported.startswith("tiny_swarm_world.infrastructure")
                or imported == "tiny_swarm_world.installer"
            }
            unexpected = {
                imported
                for imported in observed
                if not any(
                    imported == allowed or imported.startswith(f"{allowed}.")
                    for allowed in allowed_imports
                )
            }
            self.assertEqual(set(), unexpected, (relative_path, unexpected))

    def test_forbidden_import_probe_fails_closed(self):
        forbidden = "tiny_swarm_world.infrastructure.adapters.command_runner"
        imported = _direct_imports_from_source(
            "from tiny_swarm_world.infrastructure.adapters.command_runner import CommandWorkflow"
        )

        self.assertIn(forbidden, imported)
        self.assertTrue(_is_forbidden_import(forbidden, "tiny_swarm_world.infrastructure"))


class TestResponsibilityBoundaryDocumentation(unittest.TestCase):
    def test_required_architecture_documents_exist(self):
        missing_documents = [
            document_name
            for document_name, document_path in REQUIRED_ARCHITECTURE_DOCUMENTS.items()
            if not document_path.is_file()
        ]

        self.assertEqual([], missing_documents)

    def test_adr_declares_target_responsibility_boundaries(self):
        adr_text = _architecture_document("adr-separate-platform-artifacts-deployment.adoc")

        missing_boundaries = [
            boundary
            for boundary in TARGET_RESPONSIBILITY_BOUNDARIES
            if f"* `{boundary}`" not in adr_text
        ]

        self.assertEqual([], missing_boundaries)

    def test_known_mixed_boundary_files_remain_documented(self):
        analysis_text = _architecture_document("responsibility-separation-analysis.md")

        undocumented_paths = [
            path
            for path in KNOWN_MIXED_BOUNDARY_FILES
            if path not in analysis_text
        ]

        self.assertEqual([], undocumented_paths)

    def test_application_service_directories_are_deliberate(self):
        service_directories = {
            path.name
            for path in APPLICATION_SERVICES_ROOT.iterdir()
            if _is_application_service_directory(path)
        }

        unexpected_directories = sorted(service_directories - ALLOWED_APPLICATION_SERVICE_DIRECTORIES)

        self.assertEqual([], unexpected_directories)

    def test_platform_application_services_have_no_infrastructure_imports(self):
        violations = [
            violation
            for root in PLATFORM_APPLICATION_SERVICE_ROOTS
            for violation in _find_forbidden_imports(
                root=root,
                forbidden_prefix="tiny_swarm_world.infrastructure",
            )
        ]

        self.assertEqual([], violations)

    def test_deployment_application_services_have_no_platform_infrastructure_imports(self):
        forbidden_prefixes = (
            "tiny_swarm_world.application.services.network",
            "tiny_swarm_world.application.services.vm",
            "tiny_swarm_world.infrastructure",
        )
        violations = [
            violation
            for root in DEPLOYMENT_APPLICATION_SERVICE_ROOTS
            for forbidden_prefix in forbidden_prefixes
            for violation in _find_forbidden_imports(
                root=root,
                forbidden_prefix=forbidden_prefix,
            )
        ]

        self.assertEqual([], violations)

    def test_deployment_owns_nexus_stack_lifecycle_service(self):
        deployment_service_file = APPLICATION_SERVICES_ROOT / "deployment" / "ensure_nexus_stack.py"
        legacy_service_file = APPLICATION_SERVICES_ROOT / "nexus" / "ensure_nexus_stack.py"
        deployment_imports = {imported for imported, _line_number in _direct_imports(deployment_service_file)}
        legacy_imports = [imported for imported, _line_number in _direct_imports(legacy_service_file)]

        self.assertTrue(deployment_service_file.is_file())
        self.assertIn(
            "tiny_swarm_world.application.ports.clients.port_deployment_gateway",
            deployment_imports,
        )
        self.assertIn(
            "tiny_swarm_world.application.ports.repositories.port_compose_file_repository",
            deployment_imports,
        )
        self.assertNotIn("tiny_swarm_world.application.ports.clients.port_nexus_client", deployment_imports)
        self.assertEqual(
            ["tiny_swarm_world.application.services.deployment.ensure_nexus_stack"],
            legacy_imports,
        )

    def test_deployment_services_do_not_import_artifact_or_nexus_repository_readiness(self):
        forbidden_prefixes = (
            "tiny_swarm_world.application.ports.clients.port_container_runtime",
            "tiny_swarm_world.application.ports.clients.port_nexus_client",
            "tiny_swarm_world.application.services.artifacts",
            "tiny_swarm_world.application.services.nexus.ensure_nexus_repository",
        )
        violations = [
            violation
            for forbidden_prefix in forbidden_prefixes
            for violation in _find_forbidden_imports(
                root=APPLICATION_SERVICES_ROOT / "deployment",
                forbidden_prefix=forbidden_prefix,
            )
        ]

        self.assertEqual([], violations)

    def test_artifact_application_services_have_no_platform_or_deployment_imports(self):
        forbidden_prefixes = (
            "tiny_swarm_world.application.services.network",
            "tiny_swarm_world.application.services.vm",
            "tiny_swarm_world.application.services.deployment",
            "tiny_swarm_world.application.services.nexus.ensure_nexus_stack",
            "tiny_swarm_world.application.ports.clients.port_portainer_client",
            "tiny_swarm_world.application.ports.repositories.port_compose_file_repository",
            "tiny_swarm_world.infrastructure",
        )
        violations = [
            violation
            for root in ARTIFACT_APPLICATION_SERVICE_ROOTS
            for forbidden_prefix in forbidden_prefixes
            for violation in _find_forbidden_imports(
                root=root,
                forbidden_prefix=forbidden_prefix,
            )
        ]

        self.assertEqual([], violations)

    def test_cli_commands_delegate_to_composition_and_application_actions(self):
        entrypoint_text = CLI_ENTRYPOINT.read_text(encoding="utf-8")
        registry_text = (
            SOURCE_ROOT / "infrastructure" / "adapters" / "cli" / "registry.py"
        ).read_text(encoding="utf-8")
        dispatcher_text = (
            SOURCE_ROOT / "infrastructure" / "adapters" / "cli" / "dispatcher.py"
        ).read_text(encoding="utf-8")
        composition_text = (
            SOURCE_ROOT / "infrastructure" / "composition_cli.py"
        ).read_text(encoding="utf-8")
        action_text = (
            APPLICATION_SERVICES_ROOT / "cli_dispatch.py"
        ).read_text(encoding="utf-8")

        required_snippets = (
            'CliWorkflow(namespace="artifacts", action="prepare", mutating=True, destructive=False)',
            'CliWorkflow(namespace="artifacts", action="verify", mutating=False, destructive=False)',
            'CliWorkflow(namespace="deployment", action="bootstrap", mutating=True, destructive=False)',
            'CliWorkflow(namespace="deployment", action="apply", mutating=True, destructive=False)',
            'CliWorkflow(namespace="deployment", action="verify", mutating=False, destructive=False)',
            "platform_kind=kind",
        )

        missing_snippets = [
            snippet
            for snippet in required_snippets
            if snippet not in registry_text
        ]

        self.assertEqual([], missing_snippets)
        self.assertIn("execute_cli_workflow(", dispatcher_text)
        self.assertIn("await dispatcher.main(argv)", entrypoint_text)
        self.assertIn("build_artifact_services(", composition_text)
        self.assertIn("build_deployment_services(", composition_text)
        self.assertIn("run_artifact_action(", action_text)
        self.assertIn("run_deployment_action(", action_text)
        self.assertNotIn("await workflows.prepare.run()", entrypoint_text)
        self.assertNotIn("await workflows.apply.run()", entrypoint_text)

    def test_console_ui_does_not_introduce_browser_frontend_surface(self):
        forbidden_terms = (
            "react",
            "vite",
            "next",
            "tsx",
            "jsx",
            "package.json",
            "browser route",
            "api client ui",
        )
        violations = []
        for source_file in sorted(CONSOLE_UI_INFRASTRUCTURE_ROOT.rglob("*.py")):
            text = source_file.read_text(encoding="utf-8").lower()
            violations.extend(
                (source_file.relative_to(REPOSITORY_ROOT).as_posix(), term)
                for term in forbidden_terms
                if term in text
        )

        self.assertEqual([], violations)

    def test_console_ui_adapters_remain_presentation_only(self):
        forbidden_prefixes = (
            "tiny_swarm_world.application.services.artifacts",
            "tiny_swarm_world.application.services.commands",
            "tiny_swarm_world.application.services.deployment",
            "tiny_swarm_world.application.services.nexus",
            "tiny_swarm_world.application.services.platform",
            "tiny_swarm_world.application.services.setup",
            "tiny_swarm_world.infrastructure.adapters.clients",
            "tiny_swarm_world.infrastructure.adapters.command_runner",
            "tiny_swarm_world.infrastructure.composition",
        )
        violations = [
            violation
            for forbidden_prefix in forbidden_prefixes
            for violation in _find_forbidden_imports(
                root=CONSOLE_UI_INFRASTRUCTURE_ROOT,
                forbidden_prefix=forbidden_prefix,
            )
        ]

        self.assertEqual(violations, [])

    def test_nexus_artifact_repository_contracts_do_not_import_deployment_or_infrastructure(self):
        repository_contract_file = APPLICATION_SERVICES_ROOT / "nexus" / "ensure_nexus_repository.py"
        forbidden_prefixes = (
            "tiny_swarm_world.application.services.deployment",
            "tiny_swarm_world.application.services.nexus.ensure_nexus_stack",
            "tiny_swarm_world.application.ports.clients.port_portainer_client",
            "tiny_swarm_world.application.ports.repositories.port_compose_file_repository",
            "tiny_swarm_world.infrastructure",
        )
        violations = [
            violation
            for forbidden_prefix in forbidden_prefixes
            for violation in _find_forbidden_imports(
                root=repository_contract_file.parent,
                forbidden_prefix=forbidden_prefix,
            )
            if violation[0].endswith(".ensure_nexus_repository")
        ]

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
    return _direct_imports_from_tree(ast.parse(source_file.read_text(encoding="utf-8")))


def _direct_imports_from_source(source: str) -> list[str]:
    return [imported for imported, _line_number in _direct_imports_from_tree(ast.parse(source))]


def _direct_imports_from_tree(tree: ast.AST) -> list[tuple[str, int]]:
    imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((alias.name, node.lineno) for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append((node.module, node.lineno))
    return imports


def _is_forbidden_import(imported: str, forbidden_prefix: str) -> bool:
    return imported == forbidden_prefix or imported.startswith(f"{forbidden_prefix}.")


def _is_application_service_directory(path: Path) -> bool:
    if not path.is_dir() or path.name.startswith("__"):
        return False
    return any(
        source_file.is_file() and "__pycache__" not in source_file.parts
        for source_file in path.rglob("*.py")
    )


def _find_direct_filesystem_calls(root: Path) -> list[tuple[str, str, int]]:
    violations: list[tuple[str, str, int]] = []
    for source_file in sorted(root.rglob("*.py")):
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in DIRECT_FILESYSTEM_METHODS:
                continue
            if _is_storage_port_call(node.func.value):
                continue
            violations.append((_module_name(source_file), node.func.attr, node.lineno))
    return violations


def _is_storage_port_call(receiver: ast.expr) -> bool:
    if isinstance(receiver, ast.Name):
        return receiver.id == "storage"
    return isinstance(receiver, ast.Attribute) and receiver.attr == "storage"


def _architecture_document(document_name: str) -> str:
    return REQUIRED_ARCHITECTURE_DOCUMENTS[document_name].read_text(encoding="utf-8")


def _non_stdlib_imports(source: str) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                violations.append("relative import")
                continue
            names = [node.module or ""]
        else:
            continue
        violations.extend(name for name in names if name.split(".")[0] not in sys.stdlib_module_names)
    return violations


def _find_unsafe_operation_objects(value: object) -> list[str]:
    """Inspect real boundary objects before serialization can hide unsafe values."""
    violations: list[str] = []
    visited: set[int] = set()

    def visit(item: object) -> None:
        if id(item) in visited:
            return
        visited.add(id(item))
        if isinstance(item, (BaseException, TracebackType)):
            violations.append(type(item).__name__)
        elif is_dataclass(item) and not isinstance(item, type):
            for field in fields(item):
                visit(getattr(item, field.name))
        elif isinstance(item, Mapping):
            for key, member in item.items():
                visit(key)
                visit(member)
        elif isinstance(item, (tuple, list, set, frozenset)):
            for member in item:
                visit(member)

    visit(value)
    return violations


def _find_parser_objects(value: object) -> list[str]:
    """Inspect actual model fields without serialization hiding parser subclasses."""
    violations: list[str] = []
    visited: set[int] = set()

    def visit(item: object) -> None:
        if id(item) in visited:
            return
        visited.add(id(item))
        module = type(item).__module__
        if any(_is_forbidden_import(module, prefix) for prefix in FORBIDDEN_CORE_PARSER_IMPORTS):
            violations.append(module)
        if is_dataclass(item) and not isinstance(item, type):
            for field in fields(item):
                visit(getattr(item, field.name))
        elif isinstance(item, BaseModel):
            for name in type(item).model_fields:
                visit(getattr(item, name))
        elif isinstance(item, Mapping):
            for key, member in item.items():
                visit(key)
                visit(member)
        elif isinstance(item, (tuple, list, set, frozenset)):
            for member in item:
                visit(member)

    visit(value)
    return violations
