# Context Pack — Issue #189

- Workflow: `issue-189-20260809`
- Set: `solid-refactor-chain-20260809`
- Authoring branch: `feature/workflow-solid-refactor-chain-20260809`
- Execution profile: `FULL_PATH`
- Affected areas: LXC command mapping, shared diagnostics/utilities,
  composition, architecture tests and evidence.
- Forbidden areas: domain/application redesign, React/browser product work,
  live Incus/LXD/Docker/Swarm mutation, unrelated issue scopes.
- Required roles: Senior Requirement Engineer, Senior System Architect, Senior
  Python Automation Developer, Senior Tester.
- Conditional roles: Senior Documentation Engineer, Senior Security Sandbox
  Engineer, Senior Execution Orchestrator.
- Quality commands: `python3 tools/quality_gate.py quality`; targeted `lint`,
  `typecheck`, `test`, `arch-lint`, `arch-tests`; docs `git diff --check`.
- The root active workflow and root context pack remain the Issue #188
  baseline until this indexed workflow is promoted.
