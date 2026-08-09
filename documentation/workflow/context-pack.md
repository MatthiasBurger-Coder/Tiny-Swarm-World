# Context Pack — Issue #187

- Workflow: `issue-187-20260809`; chain order 04.
- Authoring branch: `feature/workflow-solid-refactor-chain-20260809`.
- Active workflow branch: `feature/preflight-service-probe-registry-solid`.
- Status: `EXECUTING_LOCAL`.
- Execution profile: `FULL_PATH`.
- Affected areas: HostPreflightProbe service matching, probe strategies,
  registry, deterministic tests and evidence.
- Forbidden areas: host detection redesign, live service checks without consent,
  browser React and unrelated stack/evidence changes.
- Required roles: Senior Requirement Engineer, Senior System Architect, Senior
  Python Automation Developer, Senior Tester.
- Conditional roles: Senior Documentation Engineer, Senior Security Sandbox
  Engineer, Senior Execution Orchestrator.
- Quality commands: `python3 tools/quality_gate.py quality` plus targeted gates
  and `git diff --check`.
