# Issue Actions and Post-Action Snapshots — Issue #217

All actions used the compare-and-set policy in `deduplication-guard.md`. Each
issue was re-read immediately before mutation and immediately after mutation.
No close, reopen, relabel or body replacement was performed.

## Candidate actions

| Issue | Stable action key | Remote action | Result | Post-state |
|---:|---|---|---|---|
| #156 | `issue-217-20260809:156:KEEP_OPEN:ecdc71d94a72530905ecb0a41d2845921ad6debb` | Added current evidence/residual-work comment | `APPLIED`, comment id `5232953424` | `open`, 2 comments, updated `2026-08-09T18:04:12Z` |
| #163 | `issue-217-20260809:163:KEEP_OPEN:ecdc71d94a72530905ecb0a41d2845921ad6debb` | Added current evidence/residual-work comment | `APPLIED`, comment id `5232956016` | `open`, 2 comments, updated `2026-08-09T18:04:33Z` |
| #197 | `issue-217-20260809:197:KEEP_OPEN:ecdc71d94a72530905ecb0a41d2845921ad6debb` | Added current evidence/residual-work comment | `APPLIED`, comment id `5232957663` | `open`, 2 comments, updated `2026-08-09T18:04:44Z` |

## Workflow issue action

| Issue | Stable action key | Remote action | Result | Post-state |
|---:|---|---|---|---|
| #217 | `issue-217-20260809:217:REVIEW_COMPLETE:ecdc71d94a72530905ecb0a41d2845921ad6debb` | Added canonical decision summary and evidence links | `APPLIED`, comment id `5232960077` | `open`, 1 comment, updated `2026-08-09T18:05:00Z` |

## Duplicate preservation

Issues #159 and #160 were not touched and remain closed as duplicates of the
#163 scope. No duplicate action key existed before the writes, and no action
was repeated after post-state verification.

