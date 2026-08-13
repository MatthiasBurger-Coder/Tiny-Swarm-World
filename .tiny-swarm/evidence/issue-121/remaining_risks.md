# Issue #121 Remaining Risks

| Risk or open point | State | Treatment |
| --- | --- | --- |
| Local EPIC context and issue-level ownership were previously implicit. | VERIFIED_LOCAL | `documentation/arc42/01_introduction/system-unification.md` is now linked explicitly; #120/#121 remain the issue authorities. |
| No separate local audit-summary artifact exists. | VERIFIED_LOCAL | The major/minor list explicitly supplied by #121 is the bounded scope; no additional findings are invented. A future authoritative summary requires a follow-up comparison. |
| The issue-named operator contract path is stale/missing. | VERIFIED_LOCAL | The stale path and verified canonical `documentation/arc42/08_configuration/operator-configuration-contract.md` path are both recorded distinctly. |
| Live green-path evidence does not exist. | PLANNED | Remains owned by #125 and the later Public-Beta gate; no live claim is made. |
| Docker socket exposure risk remains open. | OPEN | Owned by #123, #126 and #150 security/admin-surface work. |
| Existing #127 supply-chain prerequisite needs future current-state review. | EVIDENCE_PENDING | The repository policy artifacts are indexed; no new closure claim is made here. |
| The issue branch checkpoint was integrated into the authoring branch. | VERIFIED_LOCAL | Merge commit `2e3ccaab` on `docs/workflow-public-beta-roadmap-20260812` is the current integration baseline. |

These risks are intentionally retained in the audit registers and must be
re-evaluated before #120 closure. They do not authorize live infrastructure
execution.
