import ast
import tomllib
import unittest
from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class TestPackageMetadata(unittest.TestCase):
    def _setup_keyword_values(self) -> dict[str, ast.expr]:
        setup_tree = ast.parse((REPOSITORY_ROOT / "setup.py").read_text(encoding="utf-8"))
        setup_call = next(
            node
            for node in ast.walk(setup_tree)
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "setup"
        )
        keyword_values: dict[str, ast.expr] = {}
        for keyword in setup_call.keywords:
            assert keyword.arg is not None
            keyword_values[keyword.arg] = keyword.value
        return keyword_values

    def test_pyproject_declares_package_metadata_and_cli_entrypoint(self):
        pyproject = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual("tiny-swarm-world", pyproject["project"]["name"])
        self.assertEqual(">=3.12", pyproject["project"]["requires-python"])
        self.assertEqual(
            "tiny_swarm_world.__main__:cli",
            pyproject["project"]["scripts"]["tiny-swarm-world"],
        )
        self.assertEqual(["src"], pyproject["tool"]["setuptools"]["packages"]["find"]["where"])

    def test_pyproject_dependencies_match_runtime_requirements(self):
        requirements = [
            line.strip()
            for line in (REPOSITORY_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        pyproject = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual(requirements, pyproject["project"]["dependencies"])

    def test_environment_declares_ruff_quality_tool(self):
        environment = yaml.safe_load((REPOSITORY_ROOT / "environment.yml").read_text(encoding="utf-8"))
        conda_dependencies = [
            dependency for dependency in environment["dependencies"] if isinstance(dependency, str)
        ]

        self.assertIn("ruff", conda_dependencies)
        self.assertNotIn("flake8", conda_dependencies)

    def test_package_versions_are_aligned(self):
        pyproject = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        setup_version = ast.literal_eval(self._setup_keyword_values()["version"])

        self.assertEqual(pyproject["project"]["version"], setup_version)

    def test_setup_py_keeps_legacy_console_script_compatible(self):
        keyword_values = self._setup_keyword_values()

        self.assertIn("entry_points", keyword_values)
        entry_points = ast.literal_eval(keyword_values["entry_points"])
        self.assertEqual(
            ["tiny-swarm-world=tiny_swarm_world.__main__:cli"],
            entry_points["console_scripts"],
        )


if __name__ == "__main__":
    unittest.main()
