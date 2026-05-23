import ast
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src" / "tiny_swarm_world"
DOMAIN_ROOT = SOURCE_ROOT / "domain"
APPLICATION_ROOT = SOURCE_ROOT / "application"
APPLICATION_PORTS_ROOT = APPLICATION_ROOT / "ports"
APPLICATION_SERVICES_ROOT = APPLICATION_ROOT / "services"
ARCHITECTURE_DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation" / "architecture"
PACKAGE_NAME = "tiny_swarm_world"
TARGET_RESPONSIBILITY_BOUNDARIES = ("platform", "artifacts", "deployment", "shared")
PLATFORM_APPLICATION_SERVICE_ROOTS = (
    APPLICATION_SERVICES_ROOT / "multipass",
    APPLICATION_SERVICES_ROOT / "network",
    APPLICATION_SERVICES_ROOT / "vm",
    APPLICATION_SERVICES_ROOT / "platform",
)
DEPLOYMENT_APPLICATION_SERVICE_ROOTS = (
    APPLICATION_SERVICES_ROOT / "deployment",
)
ARTIFACT_APPLICATION_SERVICE_ROOTS = (
    APPLICATION_SERVICES_ROOT / "artifacts",
)
ALLOWED_APPLICATION_SERVICE_DIRECTORIES = {
    "commands",
    "multipass",
    "network",
    "nexus",
    "vm",
    *TARGET_RESPONSIBILITY_BOUNDARIES,
}
REQUIRED_ARCHITECTURE_DOCUMENTS = (
    "responsibility-separation-analysis.md",
    "adr-separate-platform-artifacts-deployment.adoc",
    "migration-plan.md",
    "agent-split-plan.md",
)
KNOWN_MIXED_BOUNDARY_FILES = (
    "src/tiny_swarm_world/application/services/nexus/bootstrap_nexus.py",
    "infra/prepare/nexus/setup.py",
    "infra/compose/create_dockerfiles.sh",
    "infra/compose/upload_all_stacks.sh",
    "infra/prepare/prepare.sh",
    "infra/prepare/portainer/portain_setup.py",
    "infra/prepare/portainer/prepare.sh",
    "src/tiny_swarm_world/infrastructure/composition.py",
    "src/tiny_swarm_world/__main__.py",
    "infra/swarm",
)


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

    def test_application_ports_do_not_import_application_services(self):
        violations = _find_forbidden_imports(
            root=APPLICATION_PORTS_ROOT,
            forbidden_prefix="tiny_swarm_world.application.services",
        )

        self.assertEqual([], violations)


class TestResponsibilityBoundaryDocumentation(unittest.TestCase):
    def test_required_architecture_documents_exist(self):
        missing_documents = [
            document_name
            for document_name in REQUIRED_ARCHITECTURE_DOCUMENTS
            if not (ARCHITECTURE_DOCUMENTATION_ROOT / document_name).is_file()
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
            if path.is_dir() and not path.name.startswith("__")
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
            "tiny_swarm_world.application.services.multipass",
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
        self.assertIn("tiny_swarm_world.application.ports.clients.port_portainer_client", deployment_imports)
        self.assertIn(
            "tiny_swarm_world.application.ports.repositories.port_compose_file_repository",
            deployment_imports,
        )
        self.assertNotIn("tiny_swarm_world.application.ports.clients.port_nexus_client", deployment_imports)
        self.assertEqual(
            ["tiny_swarm_world.application.services.deployment.ensure_nexus_stack"],
            legacy_imports,
        )

    def test_artifact_application_services_have_no_platform_or_deployment_imports(self):
        forbidden_prefixes = (
            "tiny_swarm_world.application.services.multipass",
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


def _architecture_document(document_name: str) -> str:
    return (ARCHITECTURE_DOCUMENTATION_ROOT / document_name).read_text(encoding="utf-8")
