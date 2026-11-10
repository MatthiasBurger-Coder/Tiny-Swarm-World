# Active workflow index

Exactly one active #440 workflow is selected by issue or by the explicit root
path. Historical #355/#449 plans remain accessible in Git at `ca6902579f51c2c6d9439bf9c58dec02bfb45a93`;
the current executable workflow is #440. S440-05 binds fixture and maintenance
source pins to the active root file. Historical #449 workflow bytes remain available at the baseline commit.

| Issue | Workflow ID | Workflow path | Context pack | Branch | State | Dependencies | Blockers / order |
|---|---|---|---|---|---|---|---|
| #440 | issue-440-final-acceptance | documentation/handbook/05-development/workflow/workflow.md | documentation/handbook/05-development/workflow/context-pack.md | docs/workflow-issue440-acceptance-20261110 | ACTIVE_FOR_ISSUE_440 | Existing #441–#448 implementations; accepted lifecycle/profile ADRs; reviewed exact-source evidence | Begin S440-01; 02/03 may be disjoint, then 04→05→06→07→08→09→10→11→12; live consent, exact Incus capability and independent reviews remain gates |

| Historical plan | Disposition |
|---|---|
| Root #355 operation-results workflow | Replaced by this active parent plan; history/evidence preserved at baseline |
| Indexed #449 lifecycle qualification workflow | Superseded for #440 gap closure; old source/hash-bound approvals do not authorize this workflow; S440-05 binds current helpers to #440 |

Use the existing workflow-executor discovery rules. Do not infer a plan from
file recency or run a historical workflow by silently restoring old GO material.
