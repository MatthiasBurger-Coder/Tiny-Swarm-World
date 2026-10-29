# Workflow index

This index selects an issue-local workflow only when the user request or the
current execution explicitly identifies the issue. The existing root workflow
remains intact as the legacy/default project workflow.

| Issue | Workflow ID | Workflow path | Context pack | Branch | State | Dependencies | Blockers / order |
|---|---|---|---|---|---|---|---|
| #449 | `issue-449-lcm-w09` | `documentation/workflow/issues/issue-449/workflow.md` | `documentation/workflow/issues/issue-449/context-pack.md` | `feature/lcm-w09-issue449-implementation-20261027` | `ACTIVE_FOR_ISSUE_449` | #440; #444; #446; #447; #448 | User-authorized issue execution, with fresh same-hash reviews and phase-specific S3D required for every slice. Completed: 01, 02C, 02D, 02E. S449-02F and F2 native checks remain BLOCKED on service/executable identity; no artifact or host mutation. F3 symbolic native diagnosis returned SNAP_EXECUTABLE_OUTSIDE_ROOT. S449-02F4 v1.41 defines the same-slice four-property empty-array correction; current execution/review/quality/native history is recorded only in its consolidation. Future native inventory requires its own post-commit exact-source plan and GO. Conditional 02G native maintenance requires exclusive TSW ownership; 02H WSL feature applicability and dependent policy/host scenarios remain. Native and WSL2 live installation, upgrade, failure/recovery and cleanup acceptance scenarios remain open; #449 must stay open. |

Historical v1.43 authoring snapshot: The 2026-10-29 post-commit native inventory returned
`BLOCKED:SNAP_WRAPPER_CONTEXT_BLOCKED` without an artifact. Workflow v1.43
planned S449-02F5; its implementation and bounded native diagnosis subsequently ran as noted below. It does not
establish a native inventory, ownership, support or live GO. S449-02F remains
blocked until a new complete inventory succeeds; S449-02H retains its explicit
S449-02F dependency.

Historical v1.44 authoring snapshot: native F5 source 04a0c3cf3b641775cad59da12a7951e0eb5035cc
returned BLOCKED_UNKNOWN / DROPIN_CONTENT, exit 2. S449-02F6 is PLANNED as a
separate structural diagnosis; implementation, quality and separate host GO
remain open. S449-02F remains BLOCKED and 02G/02H prerequisites remain intact.
No inventory pass, ownership, support or host mutation is claimed.

Preserved root workflow: `documentation/workflow/workflow.md` remains the
#355 workflow. It is not selected for a request explicitly targeting #449.

Selection rules are defined in
[workflow-executor](../../.agents/skills/workflow-executor/SKILL.md). Do not
infer an issue workflow from file recency or execute an indexed workflow whose
branch, context pack or status cannot be verified.

Code-only publication amendment v1.42: issue449 S449-C01→C02→C03→C04 integrates the exact86candidate in PR #499 under local-quality/required-CI authority. Live evidence is excluded for this publication; #449 and future S02/S03–S09 capability/qualification work remain INCOMPLETE. See issue-local workflow for exact files/locks and root consolidation for actual execution state.

Workflow v1.45: native F6 source 4f52873330b665ab013b607c26d7172194ff375b
returned BLOCKED_UNKNOWN / DEPENDENCY_VARIANT, exit 2. S449-02F7 is PLANNED
as a source-bound read-only generator-form diagnosis. F6 private evidence
requires independent validation. S449-02F remains BLOCKED; 02G/02H retain
their successful-inventory prerequisites. No F7 implementation or host GO
is claimed.

Workflow v1.46: native F7 source fd8dd1478329ee00a907822b4e43b19efc14a631
returned BLOCKED_UNKNOWN / UNKNOWN, exit 2. S449-02F8 is PLANNED as a closed,
typed reproducible failure-stage diagnostic; private evidence needs independent
review. F4–F7 stay unchanged; S449-02F remains BLOCKED, 02G/02H retain
prerequisites. No F8 implementation, host GO, identity or inventory pass claimed.
