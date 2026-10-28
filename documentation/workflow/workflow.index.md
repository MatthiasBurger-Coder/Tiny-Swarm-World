# Workflow index

This index selects an issue-local workflow only when the user request or the
current execution explicitly identifies the issue. The existing root workflow
remains intact as the legacy/default project workflow.

| Issue | Workflow ID | Workflow path | Context pack | Branch | State | Dependencies | Blockers / order |
|---|---|---|---|---|---|---|---|
| #449 | `issue-449-lcm-w09` | `documentation/workflow/issues/issue-449/workflow.md` | `documentation/workflow/issues/issue-449/context-pack.md` | `feature/lcm-w09-issue449-implementation-20261027` | `ACTIVE_FOR_ISSUE_449` | #440; #444; #446; #447; #448 | User-authorized issue execution, with fresh same-hash reviews and phase-specific S3D required for every slice. Completed: 01, 02C, 02D, 02E. Next: 02F bounded read-only native LXD/Incus inventory. Conditional 02G native maintenance only after exclusive TSW ownership is proven; 02H WSL feature applicability then either exact Windows-host GO/restart or conditional 02I Store-Wsl policy/tests. Existing route capture, WSL feature preflight and native service ownership blockers remain; no host mutation is authorized by this status. |

Preserved root workflow: `documentation/workflow/workflow.md` remains the
#355 workflow. It is not selected for a request explicitly targeting #449.

Selection rules are defined in
[workflow-executor](../../.agents/skills/workflow-executor/SKILL.md). Do not
infer an issue workflow from file recency or execute an indexed workflow whose
branch, context pack or status cannot be verified.
