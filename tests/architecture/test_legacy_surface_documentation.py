import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
INFRA_ROOT = REPOSITORY_ROOT / "infra"


class TestLegacySurfaceDocumentation(unittest.TestCase):
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
