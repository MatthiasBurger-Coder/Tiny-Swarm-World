import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
INFRA_ROOT = REPOSITORY_ROOT / "infra"
REMOVED_MARKER_BOUNDARIES = ("platform", "artifacts", "deployment", "shared")


class TestInfraResponsibilityBoundaries(unittest.TestCase):
    def test_empty_target_boundary_markers_are_not_reintroduced(self):
        reintroduced_boundaries = [
            boundary
            for boundary in REMOVED_MARKER_BOUNDARIES
            if (INFRA_ROOT / boundary).exists()
        ]

        self.assertEqual(reintroduced_boundaries, [])
