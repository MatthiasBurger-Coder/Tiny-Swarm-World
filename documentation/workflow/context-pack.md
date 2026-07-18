# Context Pack: SonarCloud S3415 repair

- Workflow: `workflow-sonar-s3415-20260718`
- Branch: `fix/workflow-sonar-s3415-20260718`
- Baseline: `main@e91ca5824e823fbd2ae547c23080e8847ef55ccb`
- Scope: SonarCloud-reported `python:S3415` assertion argument order in tests.
- Forbidden: production code, Sonar suppressions/profile changes, test exclusion,
  live infrastructure.
- Required checks: changed tests, `python3 tools/quality_gate.py quality`,
  `git diff --check`, followed by SonarCloud branch analysis.
- Governing files: `AGENTS.md`, `QUALITY.md`,
  `.agents/skills/workflow-slice-execution/SKILL.md`.
