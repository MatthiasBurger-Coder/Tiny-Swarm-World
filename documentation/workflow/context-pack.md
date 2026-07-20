# Workflow Context Pack

Workflow: `workflow-skill-agent-governance-20260720`
Version: `workflow-skill-agent-governance-v1.0.0`
Branch: `feature/workflow-skill-agent-governance-20260720`
Process strand: `workflow execute` after authoring
Execution profile: `FULL_PATH`

Affected areas: `.agents/**`, `.codex/**`, skill registry, routing,
governance-only tests and documentation.

Forbidden areas: `src/tiny_swarm_world/**`, `tests/**` product behavior,
Docker/runtime, contracts, persistence, analytics and live infrastructure.
`src/tiny_swarm_world/infrastructure/composition.py` is read-only architecture
boundary evidence.

Required roles: Senior Requirement Engineer, Senior System Architect, Senior
Python Automation Developer, Senior Tester, Skill Registry Conflict Auditor,
Senior Workflow Architect and Senior Documentation Engineer.

Workflow: `issue-218-20260720`
Branch: `feature/workflow-issue-218-20260720`
Issue: `#218`
Quality: `git diff --check`; `python3 tools/quality_gate.py quality` in WSL/Linux
when practical. Completion requires the evidence path and Issue Completion
Auditor PASS described in `workflow.md`.
