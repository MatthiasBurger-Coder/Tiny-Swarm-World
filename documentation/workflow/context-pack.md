# Context Pack — Indexed Issue Chain #163 → #156 → #197 → #152 → #144 → #146 → #147 → #148 → #145 → #151 → #153

- Workflow family: `issue-chain-163-156-197-152-144-146-147-148-145-151-153-20260809` (`v1.0.0`).
- Index: `documentation/workflow/workflow.index.md`.
- Authoring branch: `feature/workflow-issue-chain-163-156-197-152-144-146-147-148-145-151-153-20260809`.
- Baseline commit: `b8c64eaa50839fcbf4581ca819286ad13ee88300`.
- Execution profile: `FULL_PATH`.
- Process strand: `workflow-create-to-workflow-execute`.
- Scope: eleven ordered issue-local workflows with 74 granular implementation slices.
- Forbidden: live infrastructure by default, issue mutation, PR merge/cleanup,
  browser React, silent scope reduction and unverified live/external claims.
- Required roles: Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer, Senior Tester.
- Conditional roles: Senior Workflow Architect, Senior Documentation Engineer,
  Console/status UI Developer, Linux Host Preparation, Resilience Engineering,
  Quality Gate Governance and Issue Completion Auditor.
- Quality commands: `git diff --check`, targeted commands in each issue-local
  workflow and `python3 tools/quality_gate.py quality` from WSL/Linux.
- Issue-local packs: `documentation/workflow/issues/issue-<number>/`.
- Existing `documentation/workflow/workflow.md`: completed Issue #217 record,
  intentionally preserved and not the execution target for this index.

This pack is navigation context only. The index, issue-local workflows,
requirement matrices, root governance, quality policy, issue bodies, ADRs,
arc42 and repository behavior remain authoritative.
