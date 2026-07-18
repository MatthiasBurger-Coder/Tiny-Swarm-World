# Slice 01 Consolidation

- Workflow: `workflow-issue-218-fr02-filesystem-policy-20260712`
- Slice: `01` — WSL project filesystem policy
- Integration owner: Codex / Tiny Swarm World lead architect
- Execution mode: serial in the declared isolated worktree
- Live infrastructure: `NOT_RUN`
- Current decision: `LOCAL_COMPLETION_PASS_PENDING_CHECKPOINT`

## Consolidated implementation

The slice adds a typed project-filesystem assessment, a mountinfo-backed
infrastructure inspector, application evaluator and override authorizer,
owner-only local XDG evidence storage, and wiring through preflight, installer,
and setup ordering. A confirmed Windows-mounted checkout blocks before later
bootstrap or live work unless the explicit override is authorized. The exact
project path is redacted from public output; only the protected local override
evidence records it. Documentation describes the recommendation without
automatic move or copy behavior.

## Accepted specialist findings

- System Architecture and Security: defer relative `XDG_STATE_HOME` validation
  until an override evidence write is actually requested. This preserves normal
  preflight construction while failing closed for an unsafe evidence target.
- Tester and Console review: prove the non-live override branch evaluates but
  cannot authorize or write; route a realistic Windows path through the CLI
  safe serializer to prove ordering, determinism, and redaction.
- Requirement and Documentation review: align all affected documentation with
  the wording “Linux-native or WSL Linux” and reconcile the FR-2 evidence.
- Skill registry integrity: update the tracked README digest after the required
  documentation change.

## Deferred and rejected work

- No Incus, Docker, Swarm, network, service, or Windows mutation was run.
- No automatic filesystem move or copy was implemented.
- Later Issue #218 FRs remain outside this slice.
- Live acceptance, GitHub CI, SonarQube, pull request, merge, and branch
  cleanup are release-stage checks, not local completion evidence.

## Verification consolidation

- Regression-first RED evidence: recorded in the workflow evidence directory.
- Focused FR-2 suite: `PASS`, 343 tests; repeated with `CI=1`: `PASS`, 343
  tests.
- Focused remediation suite: `PASS`, 195 tests.
- Ruff lint: `PASS`.
- Import Linter: `PASS`, 3 contracts, 307 files, 716 dependencies.
- Hexagonal architecture tests: `PASS`, 18 tests.
- Mypy: `PASS`, 500 source files.
- Full unittest discovery: `PASS`, 1,495 tests, 28 expected skips.
- Aggregate quality gate: `PASS`.
- `git diff --check`: `PASS` before completion-evidence reconciliation.

The first lint attempt used the WSL system interpreter, which lacks Ruff. The
same unchanged gates were retried with the repository WSL virtual environment;
this is an environment repair, not a quality-gate waiver.

## Integration decision

The code and documentation are within FR-2 scope, fail closed for protected
evidence, and have passed local static and test gates. The independent
completion audit passed; the one-slice checkpoint commit is the next action.

## CP_RECORD

- `sliceId`: `01`
- `workflowVersion`: `workflow-issue-218-fr02-filesystem-policy-20260712`
- Slice title: `WSL project filesystem policy`
- Responsible owner: `Codex / Tiny Swarm World lead architect`
- Changed files: typed project-filesystem domain and ports; mountinfo and local
  evidence adapters; composition, preflight, installer, and CLI wiring;
  focused tests; README, arc42, usage/install, workflow, matrix, and evidence.
- Quality gates: focused 343 tests (including `CI=1`), remediation 195 tests,
  lint, architecture lint/tests, typecheck, full test (1,495/28), and aggregate
  quality all `PASS`.
- Rollback reference: revert the forthcoming single Slice-01 checkpoint commit
  from `feature/workflow-issue-218-fr02-filesystem-policy-20260712`.
- `arc42Updated`: `true`
- `adrUpdated`: `true`
