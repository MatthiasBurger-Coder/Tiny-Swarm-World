# Context Pack — Issue #191

- Workflow: `issue-191-20260809`; chain order 03.
- Authoring branch: `feature/workflow-solid-refactor-chain-20260809`.
- Active workflow branch: `feature/typed-verification-evidence-solid`.
- Status: `EXECUTING_LOCAL`.
- Execution profile: `FULL_PATH`.
- Affected areas: serialized evidence keys/classifications, lifecycle,
  preflight/deployment producers, compatibility and architecture tests.
- Forbidden areas: evidence key renaming, live infrastructure/browser runs,
  React, service extraction and unrelated scope.
- Required roles: Senior Requirement Engineer, Senior System Architect, Senior
  Python Automation Developer, Senior Tester.
- Conditional roles: Senior Documentation Engineer, Senior Security Sandbox
  Engineer, Senior Execution Orchestrator.
- Quality commands: full `python3 tools/quality_gate.py quality`, targeted
  Python/architecture gates and `git diff --check`.
