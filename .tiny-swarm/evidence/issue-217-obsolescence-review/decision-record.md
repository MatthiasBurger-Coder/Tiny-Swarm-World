# Canonical Decision Record — Issue #217

Decision record id: `issue-217-20260809/decisions/v1`
Baseline: `ecdc71d94a72530905ecb0a41d2845921ad6debb`
Allowed enum: `COMPLETED | SUPERSEDED | REDUCE_SCOPE | KEEP_OPEN | BLOCKED`

| Issue | Decision | Evidence basis | Recommended action | Closing reason |
|---:|---|---|---|---|
| #156 | `KEEP_OPEN` | Direct service-access publishers and URL/readiness producers still bypass the effective central map; targeted tests pass. | Retain open, add current evidence, complete central resolution and propagation tests. | Not applicable. |
| #163 | `KEEP_OPEN` | Three original raw literals remain at current lines 165, 166 and 194; targeted test passes; Sonar state unverified. | Retain open, correct the test fixture in one focused change, preserve #159/#160 as closed duplicates. | Not applicable. |
| #197 | `KEEP_OPEN` | Socat process management remains in composition; required dedicated behavior evidence is incomplete. | Retain open, extract to infrastructure adapter and add missing safety/process tests. | Not applicable. |

## Canonical interpretation

No issue is completed or superseded. The audit workflow itself has a complete
current-state decision set, but the three candidate issues remain open because
their product/quality/architecture acceptance criteria are materially
incomplete. This distinction prevents duplicate closure based on historical
assumptions.

## Duplicate and supersession relationships

Issue #163 consolidates older #159 and #160. Both remain closed as duplicates;
the workflow does not reopen them, copy their work into a new task, or infer
that #163 is complete merely because the older issues are closed.

