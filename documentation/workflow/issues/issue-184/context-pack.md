# Context Pack — Issue #184

- Workflow: `issue-184-20260809`; chain order 02.
- Authoring branch: `feature/workflow-solid-refactor-chain-20260809`.
- Execution profile: `FULL_PATH`.
- Affected areas: LXC node provider command/node/profile/resource/evidence
  boundaries, compatibility imports, architecture tests.
- Forbidden areas: public port redesign, live LXC/Swarm mutation, React/browser
  product work, #191 typed contract changes before its workflow.
- Required roles: Senior Requirement Engineer, Senior System Architect, Senior
  Python Automation Developer, Senior Tester.
- Conditional roles: Senior Documentation Engineer, Senior Security Sandbox
  Engineer, Senior Execution Orchestrator.
- Quality commands: `python3 tools/quality_gate.py quality`, targeted Python
  gates and `git diff --check`.
