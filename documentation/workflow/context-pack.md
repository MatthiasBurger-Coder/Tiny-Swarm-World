# Workflow Context Pack

Workflow: `issue-218-20260720`
Version: `issue-218-v1.1.0`
Branch: `docs/issue-218-live-acceptance-20260720`
Process strand: `workflow execute` continuation
Execution profile: `FULL_PATH`

Affected areas: `src/tiny_swarm_world/**`, `tests/**`, `tools/windows/**`,
`infra/config/**`, `documentation/**`, `.tiny-swarm/evidence/issue-218/**` and
`.codex/evidence/**` for issue completion.

Forbidden areas: secrets and unrelated governance changes. Live infrastructure
is allowed only through the explicit, bounded Issue #218 live-validation steps.

Required roles: Senior Requirement Engineer, Senior System Architect, Senior
Python Automation Developer, Senior Tester, Skill Registry Conflict Auditor,
Senior Workflow Architect and Senior Documentation Engineer.

Workflow: `issue-218-20260720`
Branch: `docs/issue-218-live-acceptance-20260720`
Issue: `#218`
Quality: `git diff --check`; `python3 tools/quality_gate.py quality` in WSL/Linux
when practical. Completion requires the evidence path and Issue Completion
Auditor PASS described in `workflow.md`.
