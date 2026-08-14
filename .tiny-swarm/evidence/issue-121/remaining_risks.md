# Issue #121 Remaining Risks

| Risk or open point | State | Treatment |
| --- | --- | --- |
| EPIC ownership | RESOLVED_AS_GOVERNANCE_LINK | System Unification explicitly owns the repository-level audit-evidence backbone; this does not close findings or authorize live work. |
| Audit-summary source | RESOLVED_AS_LOCAL_SNAPSHOT | `documentation/audit/audit-summary.md` snapshots the five major and eight minor findings explicitly supplied by #120/#121; findings outside those sources require a new reviewed source. |
| The issue-named operator contract path is stale/missing. | RESOLVED_AS_PATH_DRIFT | The stale path and verified canonical `documentation/arc42/08_configuration/operator-configuration-contract.md` path are both recorded distinctly. |
| Live green-path evidence does not exist. | PLANNED | Remains owned by #125 and the later Public-Beta gate; no live claim is made. |
| Docker socket exposure risk remains open. | OPEN | Owned by #123, #126 and #150 security/admin-surface work. |
| Existing #127 supply-chain prerequisite needs future current-state review. | EVIDENCE_PENDING | The repository policy artifacts are indexed; no new closure claim is made here. |
| Branch checkpoint is pushed but not merged into the shared integration line. | RESOLVED_AS_PR_MERGED | PR #254 merged the issue branch into `main` as `a335fed0`; the remote branch was deleted after verification. |

These risks are intentionally retained in the audit registers and must be
re-evaluated before #120 closure. They do not authorize live infrastructure
execution.
