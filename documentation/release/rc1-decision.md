# Classic Public Beta RC1 decision

Decision state: RC1_ACCEPTED

Qualification date: 2026-09-13. Integrated qualification candidate:
`69f040a75fa8a7bc9b9c01bf5eb62f53abeb6a6e`. Frozen product candidate: `c921e69533450fba86d908e2990c106bef87769a`.
The runtime, tests, configuration, tooling and CI inputs are unchanged between
these revisions; exact comparison is recorded in the
[candidate provenance](../../.tiny-swarm/evidence/issue-302/candidate-provenance.json).
The previous evidence-incomplete decision is superseded by the executed results
below; its failed and incomplete runs remain in Git/history and issue packages.

| Work package | Evidence | Result |
|---|---|---|
| R01 / #297 | [Requirement matrix](../../.tiny-swarm/evidence/issue-297/requirement_matrix.md); [PR #338](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/pull/338) | VERIFIED — Canonical update, task convergence, original-direction recovery, no-op repeats and state preservation on both hosts |
| R02 / #298 | [Requirement matrix](../../.tiny-swarm/evidence/issue-298/requirement_matrix.md); [PR #340](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/pull/340) | VERIFIED — Actual native fresh/reconcile/update/recovery, full authentication and whole-VM reboot |
| R03 / #299 | [Requirement matrix](../../.tiny-swarm/evidence/issue-299/requirement_matrix.md); [PR #339](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/pull/339) | VERIFIED — WSL lifecycle, partial failure/recovery, prerequisite fixtures and planned restart with authentication |
| R04 / #300 | [Requirement matrix](../../.tiny-swarm/evidence/issue-300/requirement_matrix.md); [PR #336](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/pull/336) | VERIFIED — Candidate-specific main/PR Sonar, locked dependencies, SBOM and container configuration scan |
| R05 / #301 | [Requirement matrix](../../.tiny-swarm/evidence/issue-301/requirement_matrix.md); [PR #337](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/pull/337) | VERIFIED — Real protected fresh hosted 14-operation lifecycle and controlled blocked dispatch |
| R06 / #302 | [Requirement matrix](../../.tiny-swarm/evidence/issue-302/requirement_matrix.md) | VERIFIED — Complete source requirements, current/historical applicability, final evidence and decision |
| R07 / #308 | [Requirement matrix](../../.tiny-swarm/evidence/issue-308/requirement_matrix.md); [PR #342](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/pull/342) | VERIFIED — Executed qualified first-user journey, resources/timing and corrected rendered manuals |
| R08 / #309 | [Requirement matrix](../../.tiny-swarm/evidence/issue-309/requirement_matrix.md); [PR #341](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/pull/341) | VERIFIED — 40 observed task images across two hosts, 16 bounded admin/network checks and owned risk dispositions |
| R09 / #310 | [Requirement matrix](../../.tiny-swarm/evidence/issue-310/requirement_matrix.md); [PR #332](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/pull/332) | VERIFIED — Actual independent Poincare/Faraday maintenance triage, with owned nonblocking #329/#331 |

Both fresh host chains pass all 14 operations, including four authenticated
phases with 25 live tests and seven API checks each. Hosted execution is
8eb5db33 (whole tree equals c921); native execution is c921. Actual executed
SHAs and timings remain in their artifacts. Credentials/overrides are covered
by the [original independent credential audit](../../.tiny-swarm/evidence/issue-277/completion_audit.md),
[CRED-09 actual transitions](../../.tiny-swarm/evidence/issue-296/test_results.md)
and [current applicability review](../../.tiny-swarm/evidence/issue-302/credential-applicability.json).

Integrated main checks: [Quality 34729686799](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/actions/runs/34729686799),
[Conda 3.12/3.13 34729686818](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/actions/runs/34729686818)
and [actual main Sonar 34729827923](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/actions/runs/34729827923)
passed. The scanner explicitly identifies 69f040a7. The successful protected
[fresh lifecycle 34725969899](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/actions/runs/34725969899)
is reused only with the exact product/whole-tree comparison. The intentionally
[blocked dispatch 34729909225](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/actions/runs/34729909225)
failed before mutation on restored runner 23; that failure is expected guard
evidence, not a successful live chain.

The [complete row audit](../../.tiny-swarm/evidence/issue-302/traceability.md)
includes every #252 body/CI requirement, all twelve mandatory scenarios and the
credential parent scope. Final review uses the explicit root-AGENTS sequential
requirement/architecture/QA fallback after real agents reached their usage limit;
it is not represented as another independent human or agent approval. Earlier
actual independent credential and maintenance reviews retain their identities.
See the [completion audit](../../.tiny-swarm/evidence/issue-302/completion_audit.md).

Acceptance is bounded to the isolated internal-test Classic profile and the
documented planned WSL restart. The failed first WSL restart and its manual
repair remain recorded. Hard power loss, arbitrary credential rotation and
production hardening are outside tested scope. Container configuration and
locked Python dependencies were scanned; built-image package vulnerability-free
status is not claimed. Socket exposure, mutable tags and internal TLS-probe
limits have explicit [R08 risk dispositions](../../.tiny-swarm/evidence/issue-309/risk-dispositions.md).

The evidence-publication PR and final merge require their own exact-revision
Quality/Conda/Sonar results before administrative closure. Their actual final
SHA and run IDs are bound in the linked PR/#294/#302 integration record; a
document cannot embed its own future commit hash. This decision qualifies the
recorded candidate and does not create a tag or publish a release.
