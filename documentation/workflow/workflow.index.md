# Workflow index

This index selects an issue-local workflow only when the user request or the
current execution explicitly identifies the issue. The existing root workflow
remains intact as the legacy/default project workflow.

| Issue | Workflow ID | Workflow path | Context pack | Branch | State | Dependencies | Blockers / order |
|---|---|---|---|---|---|---|---|
| #449 | `issue-449-lcm-w09` | `documentation/workflow/issues/issue-449/workflow.md` | `documentation/workflow/issues/issue-449/context-pack.md` | `feature/lcm-w09-issue449-implementation-20261027` | `ACTIVE_FOR_ISSUE_449` | #440; #444; #446; #447; #448 | User-authorized issue execution, with fresh same-hash reviews and phase-specific S3D required for every slice. Completed: 01, 02C, 02D, 02E. S449-02F and F2 native checks remain BLOCKED on service/executable identity; no artifact or host mutation. Next: sequential S449-02F3 symbolic path-shape classification using only in-memory data, then use fresh S3D/reviews for any further diagnosis. Conditional 02G native maintenance requires exclusive TSW ownership; 02H WSL feature applicability and dependent policy/host scenarios remain. Native and WSL2 live installation, upgrade, failure/recovery and cleanup acceptance scenarios remain open; #449 must stay open. |

Preserved root workflow: `documentation/workflow/workflow.md` remains the
#355 workflow. It is not selected for a request explicitly targeting #449.

Selection rules are defined in
[workflow-executor](../../.agents/skills/workflow-executor/SKILL.md). Do not
infer an issue workflow from file recency or execute an indexed workflow whose
branch, context pack or status cannot be verified.
