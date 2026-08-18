from __future__ import annotations

from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_ROOT = REPOSITORY_ROOT / ".github" / "workflows"


class CiWorkflowContractTests(unittest.TestCase):
    def test_python_quality_gate_runs_the_canonical_gate_on_push_and_pull_request(self) -> None:
        workflow = self._workflow("python-quality-gate.yml")

        self.assertIn("name: Python Quality Gate", workflow)
        self.assertIn("  push:", workflow)
        self.assertIn("  pull_request:", workflow)
        self.assertIn("python3 tools/quality_gate.py quality", workflow)
        self.assertIn("pip install --require-hashes -r requirements.lock", workflow)
        self.assertIn("pip install --no-deps -e .", workflow)
        self.assertIn("actions/upload-artifact@", workflow)
        self.assertIn("if-no-files-found: error", workflow)
        self.assertNotIn("pip install -r requirements-dev.txt", workflow)
        self.assertNotIn("install.sh", workflow)
        self.assertNotIn("docker swarm", workflow)
        self.assertNotIn("incus", workflow.lower())

    def test_quality_tool_installation_is_explicitly_pinned(self) -> None:
        workflow = self._workflow("python-quality-gate.yml")

        for requirement in (
            "coverage==7.15.4",
            "import-linter==2.13",
            "mypy==2.3.1",
            "pip-audit==2.10.1",
            "pip-tools==7.6.1",
            "ruff==0.15.22",
            "types-PyYAML==6.0.12.20260518",
            "types-requests==2.33.0.20260712",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(f'"{requirement}"', workflow)

    def test_sonar_workflow_owns_external_analysis_only(self) -> None:
        workflow = self._workflow("sonar_check.yml")

        self.assertIn("workflow_run:", workflow)
        self.assertIn("workflows: [Python Quality Gate]", workflow)
        self.assertIn("actions/download-artifact@", workflow)
        self.assertIn("sonar-coverage-${{ github.event.workflow_run.id }}", workflow)
        self.assertIn("github.event.workflow_run.conclusion != 'success'", workflow)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", workflow)
        self.assertIn("Require SonarCloud Token", workflow)
        self.assertIn("external gate is not green", workflow)
        self.assertIn("exit 1", workflow)
        self.assertIn("SonarSource/sonarqube-scan-action@", workflow)
        self.assertNotIn("tools/quality_gate.py quality", workflow)
        self.assertNotIn("Skip SonarCloud Scan", workflow)

    def test_sonar_workflow_requires_the_locked_runtime_contract(self) -> None:
        workflow = self._workflow("sonar_check.yml")

        self.assertIn('python-version: "3.12"', workflow)
        self.assertIn("pip install --require-hashes -r requirements.lock", workflow)
        self.assertIn("pip install --no-deps -e .", workflow)
        self.assertIn("python3 -m pip check", workflow)

    def _workflow(self, name: str) -> str:
        return (WORKFLOW_ROOT / name).read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
