from __future__ import annotations

import unittest
from pathlib import Path

from tiny_swarm_world.infrastructure import composition


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src" / "tiny_swarm_world"
FORBIDDEN_GLOBAL_DI_MARKERS = (
    "infra_core_container",
    "infra_core_di_",
    "service_locator",
    "servicelocator",
    "dependency_injection",
)


class TestExplicitCompositionBindings(unittest.TestCase):
    def test_composition_exposes_explicit_builder_functions(self) -> None:
        self.assertTrue(callable(composition.build_application_services))
        self.assertTrue(callable(composition.build_platform_services))
        self.assertTrue(callable(composition.build_setup_services))

    def test_public_facade_contains_no_probe_or_environment_implementation(self) -> None:
        source_path = (
            Path(__file__).parents[2]
            / "src"
            / "tiny_swarm_world"
            / "infrastructure"
            / "composition.py"
        )
        source = source_path.read_text(encoding="utf-8")

        self.assertNotIn("os.environ", source)
        self.assertNotIn("subprocess.run", source)
        self.assertNotIn("time.sleep", source)
        self.assertIn(
            "composition_configuration",
            source_path.parent.joinpath("composition_runtime.py").read_text(encoding="utf-8"),
        )
        self.assertTrue(source_path.parent.joinpath("composition_probes.py").is_file())
        self.assertTrue(source_path.parent.joinpath("composition_platform.py").is_file())
        self.assertTrue(source_path.parent.joinpath("composition_artifacts.py").is_file())
        self.assertTrue(source_path.parent.joinpath("composition_deployment.py").is_file())
        self.assertTrue(source_path.parent.joinpath("composition_setup.py").is_file())

    def test_runtime_source_contains_no_legacy_global_di_symbols(self) -> None:
        findings: list[str] = []
        for source_file in sorted(SOURCE_ROOT.rglob("*.py")):
            source = source_file.read_text(encoding="utf-8").lower()
            for marker in FORBIDDEN_GLOBAL_DI_MARKERS:
                if marker in source:
                    findings.append(f"{source_file.relative_to(REPOSITORY_ROOT)}: {marker}")

        self.assertEqual([], findings)


if __name__ == "__main__":
    unittest.main()
