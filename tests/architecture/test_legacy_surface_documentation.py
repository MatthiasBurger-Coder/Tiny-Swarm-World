import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
INFRA_ROOT = REPOSITORY_ROOT / "infra"
LIVE_SURFACE_CATALOG = (
    REPOSITORY_ROOT / "documentation" / "system" / "live-operation-surfaces.adoc"
)
NEXUS_SETUP = REPOSITORY_ROOT / "infra" / "prepare" / "nexus" / "setup.py"
DEPLOYMENT_DOC = REPOSITORY_ROOT / "documentation" / "deployment" / "system.adoc"


class TestLegacySurfaceDocumentation(unittest.TestCase):
    def test_live_operation_surface_catalog_defines_supported_statuses(self):
        catalog = _read_document(LIVE_SURFACE_CATALOG)

        for status in ("Supported", "Transitional", "Deprecated", "Legacy", "Supported Asset"):
            with self.subTest(status=status):
                self.assertIn(f"| {status} |", catalog)

    def test_live_operation_surface_catalog_classifies_key_entrypoints(self):
        catalog = _read_document(LIVE_SURFACE_CATALOG)
        expected_rows = {
            "`infra/prepare/prepare.sh`": "Transitional",
            "`infra/prepare/portainer/prepare.sh`": "Transitional",
            "`infra/prepare/portainer/portain_setup.py`": "Deprecated",
            "`infra/prepare/nexus/setup.py`": "Transitional",
            "`infra/prepare/nexus/addMavenMirror.sh`": "Deprecated",
            "`infra/prepare/nexus/addLocalDockerRepository.sh`": "Deprecated",
            "`infra/compose/create_dockerfiles.sh`": "Deprecated",
            "`infra/compose/upload_all_stacks.sh`": "Transitional",
            "`infra/config/compose/portainer/docker-compose.yml`": "Supported Asset",
            "`infra/config/compose/nexus/docker-compose.yml`": "Supported Asset",
            "`infra/compose/jenkins/docker-compose.yml`": "Supported Asset",
            "`infra/compose/swagger/docker-compose.yml`": "Supported Asset",
            "`infra/swarm/**`": "Legacy",
            "`infra/swarm/prepere.py`": "Legacy",
            "`infra/swarm/network/network_manager.py`": "Legacy",
        }

        for path, status in expected_rows.items():
            with self.subTest(path=path):
                self.assertIn(f"| {path} | {status} |", catalog)

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

    def test_nexus_bootstrap_documented_defaults_match_setup_script(self):
        setup = _read_document(NEXUS_SETUP)
        deployment_doc = _read_document(DEPLOYMENT_DOC)

        expected_defaults = {
            "TSW_PORTAINER_ENDPOINT": "local",
            "TSW_NEXUS_MAX_ATTEMPTS": "10",
            "TSW_NEXUS_WAIT_SECONDS": "5",
        }

        for environment_name, default in expected_defaults.items():
            with self.subTest(environment_name=environment_name):
                self.assertIn(f'os.getenv("{environment_name}", "{default}")', setup)
                self.assertIn(f"| `{environment_name}` | `{default}` |", deployment_doc)

    def test_swarm_legacy_area_documents_unsupported_entrypoint(self):
        readme = _read_infra_document("swarm/README.md")

        self.assertIn("prepere.py", readme)
        self.assertIn("legacy", readme.lower())
        self.assertIn("src/tiny_swarm_world/__main__.py", readme)
        self.assertIn("normal development quality checks", readme)

    def test_portainer_prepare_area_documents_transitional_duplicate(self):
        readme = _read_infra_document("prepare/portainer/README.md")

        self.assertIn("prepare.sh", readme)
        self.assertIn("portain_setup.py", readme)
        self.assertIn("transitional", readme.lower())
        self.assertIn("normal development quality checks", readme)


def _read_infra_document(relative_path: str) -> str:
    return (INFRA_ROOT / relative_path).read_text(encoding="utf-8")


def _read_document(path: Path) -> str:
    return path.read_text(encoding="utf-8")
