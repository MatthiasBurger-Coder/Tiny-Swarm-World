import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
INFRA_ROOT = REPOSITORY_ROOT / "infra"
LIVE_SURFACE_CATALOG = (
    REPOSITORY_ROOT / "documentation" / "system" / "live-operation-surfaces.adoc"
)
DEPLOYMENT_DOC = REPOSITORY_ROOT / "documentation" / "deployment" / "system.adoc"


class TestLegacySurfaceDocumentation(unittest.TestCase):
    def test_live_operation_surface_catalog_defines_supported_statuses(self):
        catalog = _read_document(LIVE_SURFACE_CATALOG)

        for status in ("Supported", "Transitional", "Deprecated", "Retired", "Legacy", "Supported Asset"):
            with self.subTest(status=status):
                self.assertIn(f"| {status} |", catalog)

    def test_live_operation_surface_catalog_classifies_key_entrypoints(self):
        catalog = _read_document(LIVE_SURFACE_CATALOG)
        expected_rows = {
            "`infra/prepare/prepare.sh`": "Retired",
            "`infra/prepare/portainer/prepare.sh`": "Retired",
            "`infra/prepare/portainer/portain_setup.py`": "Retired",
            "`infra/prepare/nexus/setup.py`": "Retired",
            "`infra/prepare/nexus/prepare.sh`": "Retired",
            "`infra/prepare/nexus/addMavenMirror.sh`": "Retired",
            "`infra/prepare/nexus/addLocalDockerRepository.sh`": "Retired",
            "`infra/prepare/nexus/test.sh`": "Retired",
            "`infra/compose/create_dockerfiles.sh`": "Retired",
            "`infra/compose/upload_all_stacks.sh`": "Retired",
            "`infra/config/compose/portainer/docker-compose.yml`": "Supported Asset",
            "`infra/config/compose/nexus/docker-compose.yml`": "Supported Asset",
            "`infra/config/compose/jenkins/docker-compose.yml`": "Supported Asset",
            "`infra/config/compose/swagger/docker-compose.yml`": "Supported Asset",
            "`infra/swarm/**`": "Legacy",
            "`infra/swarm/prepere.py`": "Legacy",
            "`infra/swarm/network/network_manager.py`": "Legacy",
        }

        for path, status in expected_rows.items():
            with self.subTest(path=path):
                self.assertIn(f"| {path} | {status} |", catalog)

    def test_compose_area_has_no_host_side_shell_orchestration(self):
        allowed_runtime_shell_assets = {
            "infra/compose/swagger/nginx/wait-for-it.sh",
        }
        shell_scripts = {
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for path in (REPOSITORY_ROOT / "infra" / "compose").rglob("*.sh")
        }

        self.assertEqual(allowed_runtime_shell_assets, shell_scripts)

        forbidden_fragments = (
            "docker build",
            "docker login",
            "docker push",
            "docker stack",
            "api/auth",
            "api/stacks",
            "portainer",
        )
        violations = {
            path: fragment
            for path in shell_scripts
            for fragment in forbidden_fragments
            if fragment in (REPOSITORY_ROOT / path).read_text(encoding="utf-8").lower()
        }

        self.assertEqual({}, violations)

    def test_compose_area_has_no_stack_definitions(self):
        stack_definitions = sorted(
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for path in (REPOSITORY_ROOT / "infra" / "compose").rglob("docker-compose.yml")
        )

        self.assertEqual([], stack_definitions)

    def test_prepare_area_has_no_executable_installation_helpers(self):
        executable_helpers = sorted(
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for suffix in ("*.sh", "*.py")
            for path in (REPOSITORY_ROOT / "infra" / "prepare").rglob(suffix)
        )

        self.assertEqual([], executable_helpers)

    def test_java_maven_project_surface_is_not_reintroduced(self):
        forbidden_paths = (
            REPOSITORY_ROOT / "pom.xml",
            REPOSITORY_ROOT / "src" / "main" / "java",
        )
        present_paths = [
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for path in forbidden_paths
            if path.exists()
        ]

        self.assertEqual([], present_paths)

    def test_operator_docs_reference_live_operation_surface_catalog(self):
        catalog_path = "documentation/system/live-operation-surfaces.adoc"
        docs = [
            REPOSITORY_ROOT / "README.md",
            REPOSITORY_ROOT / "documentation" / "deployment" / "system.adoc",
            REPOSITORY_ROOT / "documentation" / "user_guide" / "usage.adoc",
            REPOSITORY_ROOT / "documentation" / "user_guide" / "installation.adoc",
        ]

        missing_reference = [
            doc.relative_to(REPOSITORY_ROOT).as_posix()
            for doc in docs
            if catalog_path not in _read_document(doc)
        ]

        self.assertEqual([], missing_reference)

    def test_nexus_bootstrap_is_routed_through_setup_workflow(self):
        deployment_doc = _read_document(DEPLOYMENT_DOC)

        self.assertIn("PYTHONPATH=src python3 -m tiny_swarm_world setup run --live", deployment_doc)
        self.assertIn("Nexus setup is owned by the Python setup workflow", deployment_doc)
        self.assertNotIn("python3 infra/prepare/nexus/setup.py", deployment_doc)

    def test_swarm_legacy_area_documents_unsupported_entrypoint(self):
        readme = _read_infra_document("swarm/README.md")

        self.assertIn("prepere.py", readme)
        self.assertIn("legacy", readme.lower())
        self.assertIn("src/tiny_swarm_world/__main__.py", readme)
        self.assertIn("normal development quality checks", readme)

    def test_prepare_area_documents_retired_helpers(self):
        root_readme = _read_infra_document("prepare/README.md")
        readme = _read_infra_document("prepare/portainer/README.md")
        nexus_readme = _read_infra_document("prepare/nexus/README.md")

        self.assertIn("setup run --live", root_readme)
        self.assertIn("prepare.sh", readme)
        self.assertIn("portain_setup.py", readme)
        self.assertIn("retired", readme.lower())
        self.assertIn("setup.py", nexus_readme)
        self.assertIn("retired", nexus_readme.lower())


def _read_infra_document(relative_path: str) -> str:
    return (INFRA_ROOT / relative_path).read_text(encoding="utf-8")


def _read_document(path: Path) -> str:
    return path.read_text(encoding="utf-8")
