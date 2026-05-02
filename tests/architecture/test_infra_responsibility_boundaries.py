import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
INFRA_ROOT = REPOSITORY_ROOT / "infra"
TARGET_INFRA_BOUNDARIES = ("platform", "artifacts", "deployment", "shared")


class TestInfraResponsibilityBoundaries(unittest.TestCase):
    def test_target_infra_boundary_directories_are_documented(self):
        missing_readmes = [
            boundary
            for boundary in TARGET_INFRA_BOUNDARIES
            if not (INFRA_ROOT / boundary / "README.md").is_file()
        ]

        self.assertEqual([], missing_readmes)

    def test_target_infra_boundary_directories_are_markers_only(self):
        non_marker_files = []
        for boundary in TARGET_INFRA_BOUNDARIES:
            boundary_root = INFRA_ROOT / boundary
            files = [
                path.relative_to(boundary_root).as_posix()
                for path in boundary_root.rglob("*")
                if path.is_file()
            ]
            non_marker_files.extend(
                f"{boundary}/{path}"
                for path in files
                if path != "README.md"
            )

        self.assertEqual([], non_marker_files)
