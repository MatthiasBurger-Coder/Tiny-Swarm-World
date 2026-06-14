# Workflow Index: Open Issue Workflow Batch

```yaml
workflow_index_id: open-issue-workflow-batch-20260614
workflow_index_version: 1.0.0
authoring_branch: feature/workflow-index-open-issues-20260614
created_utc: "2026-06-14T00:00:00Z"
active_workflow_preserved: documentation/workflow/workflow.md
included_issue_count: 21
excluded_issue_count: 2
status: AUTHORED_INDEXED_NOT_ACTIVE
```

## Purpose

This index coordinates multiple issue-local workflows without overwriting the
single active workflow file at `documentation/workflow/workflow.md`. Each
included issue has its own `workflow.md` and context pack under
`documentation/workflow/issues/issue-<number>/`.

Unqualified `workflow execute` must not guess from this index. A workflow must
first be promoted to the active workflow path or the executor must be extended
to accept an explicit indexed workflow path.

## Included Workflows

| Order | Issue | Title | Workflow id | Workflow path | Proposed execution branch | Dependencies | Status |
|---:|---:|---|---|---|---|---|---|
| 1 | #4 | Validate Docker Swarm stack definitions | `issue-4-swarm-stack-validation-20260614` | `documentation/workflow/issues/issue-4/workflow.md` | `feature/workflow-issue-4-swarm-stack-validation-20260614` | none | AUTHORED_INDEXED_NOT_ACTIVE |
| 2 | #78 | Add standard Python packaging | `issue-78-python-packaging-20260614` | `documentation/workflow/issues/issue-78/workflow.md` | `feature/workflow-issue-78-python-packaging-20260614` | none | AUTHORED_INDEXED_NOT_ACTIVE |
| 3 | #64 | Honor backend selection order | `issue-64-backend-selection-order-20260614` | `documentation/workflow/issues/issue-64/workflow.md` | `feature/workflow-issue-64-backend-selection-order-20260614` | none | AUTHORED_INDEXED_NOT_ACTIVE |
| 4 | #65 | Make resource mapping backend aware | `issue-65-backend-resource-mapping-20260614` | `documentation/workflow/issues/issue-65/workflow.md` | `feature/workflow-issue-65-backend-resource-mapping-20260614` | none | AUTHORED_INDEXED_NOT_ACTIVE |
| 5 | #69 | Use host-specific evidence directories | `issue-69-host-evidence-directories-20260614` | `documentation/workflow/issues/issue-69/workflow.md` | `feature/workflow-issue-69-host-evidence-directories-20260614` | none | AUTHORED_INDEXED_NOT_ACTIVE |
| 6 | #68 | Replace piped installer approval with explicit flag | `issue-68-explicit-live-approval-20260614` | `documentation/workflow/issues/issue-68/workflow.md` | `feature/workflow-issue-68-explicit-live-approval-20260614` | none | AUTHORED_INDEXED_NOT_ACTIVE |
| 7 | #81 | Make install.sh complete without requiring the console TUI | `issue-81-headless-install-20260614` | `documentation/workflow/issues/issue-81/workflow.md` | `feature/workflow-issue-81-headless-install-20260614` | none | AUTHORED_INDEXED_NOT_ACTIVE |
| 8 | #67 | Move install logic from shell to Python | `issue-67-python-installer-20260614` | `documentation/workflow/issues/issue-67/workflow.md` | `feature/workflow-issue-67-python-installer-20260614` | issue-68, issue-69, issue-81 | AUTHORED_INDEXED_NOT_ACTIVE |
| 9 | #76 | Define configuration value ownership | `issue-76-configuration-value-ownership-20260614` | `documentation/workflow/issues/issue-76/workflow.md` | `feature/workflow-issue-76-configuration-value-ownership-20260614` | issue-67, issue-68 | AUTHORED_INDEXED_NOT_ACTIVE |
| 10 | #70 | Clarify command runner responsibility | `issue-70-command-runner-responsibility-20260614` | `documentation/workflow/issues/issue-70/workflow.md` | `feature/workflow-issue-70-command-runner-responsibility-20260614` | none | AUTHORED_INDEXED_NOT_ACTIVE |
| 11 | #71 | Remove placeholder automation runner | `issue-71-disable-ansible-runner-20260614` | `documentation/workflow/issues/issue-71/workflow.md` | `feature/workflow-issue-71-disable-ansible-runner-20260614` | issue-70 | AUTHORED_INDEXED_NOT_ACTIVE |
| 12 | #72 | Implement or disable REST command runner | `issue-72-rest-runner-decision-20260614` | `documentation/workflow/issues/issue-72/workflow.md` | `feature/workflow-issue-72-rest-runner-decision-20260614` | issue-70 | AUTHORED_INDEXED_NOT_ACTIVE |
| 13 | #74 | Make preflight provider aware | `issue-74-provider-aware-preflight-20260614` | `documentation/workflow/issues/issue-74/workflow.md` | `feature/workflow-issue-74-provider-aware-preflight-20260614` | none | AUTHORED_INDEXED_NOT_ACTIVE |
| 14 | #66 | Strengthen platform verify checks | `issue-66-platform-verify-checks-20260614` | `documentation/workflow/issues/issue-66/workflow.md` | `feature/workflow-issue-66-platform-verify-checks-20260614` | issue-74 | AUTHORED_INDEXED_NOT_ACTIVE |
| 15 | #77 | Decouple deployment gateway adapter | `issue-77-deployment-gateway-port-20260614` | `documentation/workflow/issues/issue-77/workflow.md` | `feature/workflow-issue-77-deployment-gateway-port-20260614` | none | AUTHORED_INDEXED_NOT_ACTIVE |
| 16 | #73 | Split oversized composition root | `issue-73-split-composition-root-20260614` | `documentation/workflow/issues/issue-73/workflow.md` | `feature/workflow-issue-73-split-composition-root-20260614` | issue-64, issue-65, issue-74, issue-77 | AUTHORED_INDEXED_NOT_ACTIVE |
| 17 | #83 | Define the status and evidence contract consumed by the console UI | `issue-83-ui-status-evidence-contract-20260614` | `documentation/workflow/issues/issue-83/workflow.md` | `feature/workflow-issue-83-ui-status-evidence-contract-20260614` | none | AUTHORED_INDEXED_NOT_ACTIVE |
| 18 | #82 | Add architecture tests that keep the console UI presentation-only | `issue-82-ui-presentation-arch-tests-20260614` | `documentation/workflow/issues/issue-82/workflow.md` | `feature/workflow-issue-82-ui-presentation-arch-tests-20260614` | issue-83 | AUTHORED_INDEXED_NOT_ACTIVE |
| 19 | #80 | Decouple command execution from the console UI adapter | `issue-80-ui-execution-decoupling-20260614` | `documentation/workflow/issues/issue-80/workflow.md` | `feature/workflow-issue-80-ui-execution-decoupling-20260614` | issue-83, issue-82 | AUTHORED_INDEXED_NOT_ACTIVE |
| 20 | #75 | Clarify status display purpose | `issue-75-status-display-purpose-20260614` | `documentation/workflow/issues/issue-75/workflow.md` | `feature/workflow-issue-75-status-display-purpose-20260614` | issue-83, issue-82 | AUTHORED_INDEXED_NOT_ACTIVE |
| 21 | #63 | Align reconcile workflow semantics | `issue-63-reconcile-semantics-20260614` | `documentation/workflow/issues/issue-63/workflow.md` | `feature/workflow-issue-63-reconcile-semantics-20260614` | none | AUTHORED_INDEXED_NOT_ACTIVE |

## Excluded Issues

| Issue | Title | Reason |
|---:|---|---|
| #5 | Collect information in structured format | Excluded by user decision and blocked by the Requirement Clarification Gate; source, target format, persistence, interface, and acceptance criteria are missing. |
| #7 | Testen | Excluded by user decision and blocked by the Requirement Clarification Gate; the issue body is the unchanged feature template and contains no actionable requirement. |

## Execution Sequencing Notes

- `#83` should execute before `#82`, `#80`, and `#75` because it defines the
  status/evidence contract consumed by console UI work.
- `#70` should execute before `#71` and `#72` because it defines command runner
  responsibility.
- `#68`, `#69`, and `#81` should execute before or alongside `#67` because the
  Python installer migration depends on consent, evidence path, and headless
  installation semantics.
- `#64`, `#65`, `#74`, and `#77` should execute before `#73` where practical to
  reduce composition-root merge conflicts.
- Live validation remains serialized for all workflows unless isolated live
  infrastructure is explicitly approved.

## Quality Expectations

Workflow authoring:

```bash
git diff --check
```

Workflow execution for promoted workflows:

```bash
python3 tools/quality_gate.py test
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py quality
```

## Governance Notes

- Root `AGENTS.md` and `QUALITY.md` remain authoritative.
- The multi-issue layout is governed by `.agents/skills/workflow-authoring/SKILL.md`.
- `#5` and `#7` are intentionally excluded by user decision and because their
  requirements are not actionable enough for executable workflow authoring.
