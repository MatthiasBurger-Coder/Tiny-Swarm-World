# Workflow index

This index selects an issue-local workflow only when the user request or the
current execution explicitly identifies the issue. The existing root workflow
remains intact as the legacy/default project workflow.

| Issue | Workflow ID | Workflow path | Context pack | Branch | State | Dependencies | Blockers / order |
|---|---|---|---|---|---|---|---|
| #449 | `issue-449-lcm-w09` | `documentation/handbook/05-development/workflow/issues/issue-449/workflow.md` | `documentation/handbook/05-development/workflow/issues/issue-449/context-pack.md` | `feature/lcm-w09-issue449-implementation-20261027` | `ACTIVE_FOR_ISSUE_449` | #440; #444; #446; #447; #448 | User-authorized issue execution, with fresh same-hash reviews and phase-specific S3D required for every slice. Completed: 01, 02C, 02D, 02E. S449-02F and F2 native checks remain BLOCKED on service/executable identity; no artifact or host mutation. F3 symbolic native diagnosis returned SNAP_EXECUTABLE_OUTSIDE_ROOT. S449-02F4 v1.41 defines the same-slice four-property empty-array correction; current execution/review/quality/native history is recorded only in its consolidation. Future native inventory requires its own post-commit exact-source plan and GO. Conditional 02G native maintenance requires exclusive TSW ownership; 02H WSL feature applicability and dependent policy/host scenarios remain. Native and WSL2 live installation, upgrade, failure/recovery and cleanup acceptance scenarios remain open; #449 must stay open. |

Preserved root workflow: `documentation/handbook/05-development/workflow/workflow.md` remains the
#355 workflow. It is not selected for a request explicitly targeting #449.

Selection rules are defined in
[workflow-executor](../../../../.agents/skills/workflow-executor/SKILL.md). Do not
infer an issue workflow from file recency or execute an indexed workflow whose
branch, context pack or status cannot be verified.

Code-only publication amendment v1.42: issue449 S449-C01→C02→C03→C04 integrates the exact86candidate in PR #499 under local-quality/required-CI authority. Live evidence is excluded for this publication; #449 and future S02/S03–S09 capability/qualification work remain INCOMPLETE. See issue-local workflow for exact files/locks and root consolidation for actual execution state.

<!-- Retained historical issue-449 slice index entries. -->
| #449 | `issue-449-lcm-w09` | `documentation/workflow/issues/issue-449/workflow.md` | `documentation/workflow/issues/issue-449/context-pack.md` | `feature/lcm-w09-issue449-implementation-20261027` | `ACTIVE_FOR_ISSUE_449` | #440; #444; #446; #447; #448 | User-authorized issue execution, with fresh same-hash reviews and phase-specific S3D required for every slice. Completed: 01, 02C, 02D, 02E. S449-02F and F2 native checks remain BLOCKED on service/executable identity; no artifact or host mutation. F3 symbolic native diagnosis returned SNAP_EXECUTABLE_OUTSIDE_ROOT. S449-02F4 v1.41 defines the same-slice four-property empty-array correction; current execution/review/quality/native history is recorded only in its consolidation. Future native inventory requires its own post-commit exact-source plan and GO. Conditional 02G native maintenance requires exclusive TSW ownership; 02H WSL feature applicability and dependent policy/host scenarios remain. Native and WSL2 live installation, upgrade, failure/recovery and cleanup acceptance scenarios remain open; #449 must stay open. |
planned S449-02F5; its implementation and bounded native diagnosis subsequently ran as noted below. It does not
establish a native inventory, ownership, support or live GO. S449-02F remains
blocked until a new complete inventory succeeds; S449-02H retains its explicit
S449-02F dependency.
returned BLOCKED_UNKNOWN / DROPIN_CONTENT, exit 2. S449-02F6 is PLANNED as a
remain open. S449-02F remains BLOCKED and 02G/02H prerequisites remain intact.
returned BLOCKED_UNKNOWN / DEPENDENCY_VARIANT, exit 2. S449-02F7 is PLANNED
requires independent validation. S449-02F remains BLOCKED; 02G/02H retain
returned BLOCKED_UNKNOWN / UNKNOWN, exit 2. S449-02F8 is PLANNED as a closed,
review. F4–F7 stay unchanged; S449-02F remains BLOCKED, 02G/02H retain
returned BLOCKED_UNKNOWN / PROCESS_BINDING, exit 2. S449-02F9 is PLANNED as
review. F4–F8 remain unchanged; S449-02F stays BLOCKED, and 02G/02H retain
Workflow v1.48 adds PLANNED S449-02F10 after F9's native `BLOCKED_UNKNOWN / PROC_ROOT` exit 2 at `4adcdfe456afddd881820c9a060a53113a2febfd`. It compares only the current F10 reader and visible PID 1 namespace under the bounded contract; the private F9 result needs review and no host admission or inventory success follows. S449-02F remains BLOCKED.
Workflow v1.49 records a S449-02F11 end-to-end host-admission proposal marked NOT_FEASIBLE for the current collector; existing blockers, graph and host requirements remain in force pending review and S3D.
