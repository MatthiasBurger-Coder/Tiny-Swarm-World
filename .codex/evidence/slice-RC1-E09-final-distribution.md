# RC1-E09 final audit preflight and distribution

Date: 2026-09-13. Owner: Codex / tiny-swarm-world-lead-architect.
Branch: `docs/rc1-r06-final-audit-20260913`, isolated worktree, clean before
audit edits. Integrated base: `69f040a75fa8a7bc9b9c01bf5eb62f53abeb6a6e`.
Selected workflow: the existing `rc1-evidence-completion-20260912` index and
issue-302 workflow in the integration checkout. FULL_PATH / S3D: serial final
integration; all eight dependent issue packages are merged. Product candidate
remains c921e695; changes after it are documentation/evidence only, subject to
the recorded source comparison and final integrated CI.

Before implementation, the existing R06-01..10 matrix is the minimum contract.
The complete #252 body and CI addendum, full #302 and #294, original #277 snapshot
and its 25-row audited matrix, and #295/#296 completion records are the sources
for the expanded row audit. The live GitHub #277 endpoint now returns HTTP 410
(deleted); this is a publication limitation, not evidence of missing credential
implementation. Preserve its original requirements and independent audit.

Scope reconciliation before edits: R06-03/10 require current-status corrections,
release notes/checklist and the user-requested workflow publication. Allowed
paths are `documentation/release/`, this issue's `.tiny-swarm/evidence/issue-302/`,
the missing six-file wrapper under `.tiny-swarm/evidence/issue-296/`, dated
appendices in issue-277 and issue-285 evidence, the nine issue workflows/context
packs and `documentation/workflow/workflow.index.md`, the historical execution
preflight, and E09 distribution/consolidation records. The credential wrapper
references existing executed evidence; it does not invent another live run.
No source, tests, configuration, CI behavior, architecture policy or unrelated
worktree is changed. GitHub checklist reconciliation is limited to #294/#302
and the final PR; no deleted issue is recreated.

Locks: release matrix, workflow metadata, issue evidence, candidate provenance.
All real specialist agents reached their usage limit during this execution.
Root AGENTS explicitly permits sequential role-based fallback. Apply separate
requirement, architecture and QA checklists; identify that fallback honestly.
Retain actual earlier independent credential and R09 reviews as such. Final
integration and publication remain Codex's responsibility.

Existing full user authorization covers the completed live runs, restoration,
PRs/merges and test-VM shutdown. Native poweroff returned zero; the additional
Windows elevated status query was cancelled and is not a verified Hyper-V
state. All native artifacts were archived before poweroff. No new request or
workaround for the cancelled status query is needed to audit the executed tests.

Required checks: complete source-to-evidence rows, existing canonical quality
gate, debugger/static preflight, source applicability, evidence integrity and
links, exact integrated Quality/Conda/Sonar results, final PR checks and merge
record. Pending checks remain pending until observed.
