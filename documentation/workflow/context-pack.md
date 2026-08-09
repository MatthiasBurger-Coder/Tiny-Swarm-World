# Active Context Pack — Issue #189

- Workflow: `issue-189-20260809`
- Workflow set: `solid-refactor-chain-20260809`
- Status: `ACTIVE_EXECUTION`
- Active workflow branch: `feature/centralize-lxc-shared-utilities-solid`
- Workflow authoring source branch: `feature/workflow-solid-refactor-chain-20260809`
- Implementation branch: `feature/centralize-lxc-shared-utilities-solid`
- Promotion source: `documentation/workflow/issues/issue-189/workflow.md`
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
- Requirement matrix: `.tiny-swarm/evidence/solid-lxc-shared-utilities/requirement_matrix.md`
- Issue-required evidence: `.tiny-swarm-world/evidence/solid-lxc-shared-utilities/`
- Chain position: #189 is first; #184 remains blocked until #189 completion and
  independent issue-completion audit.

The indexed workflow has been promoted to the active root location. No
implementation slice has been executed as part of promotion; S3/S3D preflight
remains the execution gate.
