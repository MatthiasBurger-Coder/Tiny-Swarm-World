# Active workflow index

Exactly one active #440 workflow is selected by issue or by the explicit root
path. Historical #355/#449 plans remain accessible in Git at `ca6902579f51c2c6d9439bf9c58dec02bfb45a93`;
they are not active executable workflows on this branch. The exact historical
#449 workflow file is temporarily retained as a pinned fixture input (SHA-256
`dcc35dfde66417bbee7263cfc233fca68855ef66b3001dab2831ba1dc294b395`), not an indexed active workflow or a live GO. S440-05 removes it after rebinding both consumers/tests.

| Issue | Workflow ID | Workflow path | Context pack | Branch | State | Dependencies | Blockers / order |
|---|---|---|---|---|---|---|---|
| #440 | issue-440-final-acceptance | documentation/handbook/05-development/workflow/workflow.md | documentation/handbook/05-development/workflow/context-pack.md | docs/workflow-issue440-acceptance-20261110 | ACTIVE_FOR_ISSUE_440 | Existing #441–#448 implementations; accepted lifecycle/profile ADRs; reviewed exact-source evidence | Begin S440-01; 02/03 may be disjoint, then 04→05→06→07→08→09→10→11→12; live consent, exact Incus capability and independent reviews remain gates |

| Historical plan | Disposition |
|---|---|
| Root #355 operation-results workflow | Replaced by this active parent plan; history/evidence preserved at baseline |
| Indexed #449 lifecycle qualification workflow | Superseded for #440 gap closure; old source/hash-bound approvals do not authorize this workflow; S440-05 repairs helper binding before use |

Use the existing workflow-executor discovery rules. Do not infer a plan from
file recency or run a historical workflow by silently restoring old GO material.
