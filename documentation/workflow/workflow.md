# Workflow: Issue #217 — Review Obsolescence Candidates

Workflow ID: `issue-217-20260809`

Workflow version: `issue-217-v1.0.0`

Status: `COMPLETED`

Authoring branch: `feature/workflow-review-obsolete-issues-20260809`

Implementation branch: `requirements/review-obsolete-issues-156-163-197-20260809`

## Executive Summary

Issue #217 is a requirements-governance workflow for reviewing Issues #156,
#163 and #197 against the current `main` implementation. It produces one
evidence-backed decision per issue and applies only the corresponding,
idempotent backlog action after the review is complete.

The workflow does not implement product behavior. It prevents duplicate work by
freezing the source baseline, separating the three audits, preserving known
duplicate/supersession relationships, and requiring a re-read-and-compare guard
before any GitHub issue mutation.

## Target Picture

- Every candidate issue has exactly one current-state decision:
  `COMPLETED`, `SUPERSEDED`, `REDUCE_SCOPE`, `KEEP_OPEN` or `BLOCKED`.
- Every decision is tied to current `main` source, test, evidence and
  documentation facts; commit messages are never sufficient evidence.
- Completed or superseded work is not reimplemented. Reduced-scope issues
  contain only verified residual work. Open issues do not retain stale evidence
  or obsolete acceptance criteria.
- Missing external Sonar evidence remains explicitly `unverified`.
- No live Docker, LXC, Incus, Swarm, networking or Selenium mutation occurs in
  the default path.

## Requirement Clarification Record

- Original Request: `workflow create #217 zuerst: räumt veraltete Backlog-Tickets auf und verhindert Doppelarbeit.`
- Interpreted Intent: author an executable workflow for the exact review and
  backlog decisions specified by GitHub Issue #217, without executing product
  changes or closing issues during authoring.
- Change Type: requirements review, backlog governance, evidence and external
  issue-state coordination.
- Affected Process Strand: `workflow-create-to-workflow-execute`.
- Execution Profile: `FULL_PATH`; workflow structure, branch, evidence,
  quality and external coordination rules are affected.
- Affected Architecture Area: read-only inspection of deployment port
  resolution, test fixtures and infrastructure composition; no production
  architecture change is authorized by this workflow.
- Explicit Requirements: all requirements in
  `.tiny-swarm/evidence/issue-217-obsolescence-review/requirement_matrix.md`.
- Implicit Requirements: stable evidence identity, no duplicate issue action,
  explicit unknown/unverified states, current-main provenance and no silent
  scope reduction.
- Assumptions: Issue #217 and the current bodies/comments of #156, #163 and
  #197 are the authoritative requirement sources; no matching EPIC exists.
  GitHub mutations are performed only by the final workflow slice after the
  evidence gate and only when the workflow execution authorization covers them.
- Non-Goals: product refactoring, closing issues during authoring, live
  infrastructure, browser/Selenium checks, unrelated backlog cleanup, changing
  Sonar configuration, or creating an ADR from a review hypothesis.
- Risks: the remote issue may change after the baseline; external Sonar state
  may be inaccessible; existing implementation may satisfy part of an issue
  while its acceptance wording remains stale; concurrent work may invalidate a
  decision.
- Open Questions: none blocking workflow authoring. The execution report must
  record any remote issue edit conflict or unavailable evidence.
- Blocking Questions: a missing current-main baseline, unverifiable source
  path, unavailable required local test, or remote issue drift before mutation
  blocks the affected decision/action.
- Confidence Level: 88%.
- Decision: `PROCEED_WITH_ACCEPTED_ASSUMPTIONS`.

The accepted non-blocking assumption is that no EPIC-specific acceptance
criteria exist beyond the issue bodies. This remains a traceability gap and
must not be presented as an implementation result.

## Verified Baseline

Read-only baseline at authoring time:

- `main` and `origin/main` both resolve to `ecdc71d94a72530905ecb0a41d2845921ad6debb`.
- The old active indexed workflow was a completed SOLID-refactor chain; it was
  regenerated for this new single-issue workflow on the dedicated authoring
  branch.
- Issue #217, #156, #163 and #197 are open. Each candidate issue has a comment
  routing it through #217 and explicitly saying not to close it yet.
- #156 has a central `infra/config/ports.yaml`, a typed port repository and
  effective-access/Compose test surfaces. Direct Compose published values and
  the complete URL/health/evidence path still require one consolidated audit.
- #163 still contains the original test-only IP literals in
  `tests/domain/network/test_port_forwarding_plan.py`; the original Sonar
  result is an external fact and must be classified as `unverified` when it
  cannot be observed.
- #197 still has `_WslSocatExposeStep`, Socat process inspection and subprocess
  startup helpers in `src/tiny_swarm_world/infrastructure/composition.py`.
  Existing composition tests cover the behavior, but extraction ownership must
  be decided from current source and test evidence.

These are baseline observations, not final issue decisions.

## Scope

In scope:

- current-main inventory and issue-body/criteria capture;
- Three-Amigos review for #156, #163 and #197;
- static source, configuration, test, evidence and documentation tracing;
- targeted local tests and the full local quality gate;
- one decision record per issue;
- idempotent, evidence-backed issue close/rewrite/comment actions in the final
  slice when authorized;
- required issue-completion evidence and independent auditor handoff.

Explicit non-goals:

- no implementation changes to Python, YAML, Compose, tests or deployment
  assets;
- no live Docker, Swarm, Incus, LXC, networking, Socat or Selenium commands;
- no SonarCloud claim when the external result is inaccessible;
- no issue closure based on commit history, issue age, labels or inferred
  replacement work;
- no unrelated issue triage or broad backlog deletion;
- no new EPIC, ADR or architecture decision without verified drift and owner
  approval.

## Architecture and Safety Constraints

- The review treats existing Python production paths as evidence only. It must
  not move behavior across domain, application or infrastructure boundaries.
- #197's architecture check must preserve the existing rule that composition
  constructs adapters while infrastructure owns subprocess behavior.
- #156's review distinguishes external published ports from image-specific
  internal targets and does not treat a static value as centrally resolved
  without tracing the effective model.
- All evidence is sanitized; no credentials, tokens, raw external payloads or
  host-specific secret material may be copied into the evidence package.
- Local quality is authoritative for local completion. Live and external states
  follow `documentation/process/verification-state-policy.md`.
- Issue mutations are guarded by current-state compare-and-set semantics:
  re-read the issue, verify the decision record is still current, perform one
  action, then re-read and record the result. If state changed, stop with an
  explicit conflict instead of retrying a possibly completed mutation.

## Python Automation Assessment

`FULL_PATH` review impact, `NO_IMPLEMENTATION_CHANGE`. The workflow inspects
Python deployment, composition and test code, but no Python source is writable
by any slice. If a residual requirement is discovered, the output is a
`KEEP_OPEN` or `REDUCE_SCOPE` issue action; implementation belongs to a later
explicit workflow.

## Frontend Assessment

`NOT_APPLICABLE`. No browser or React frontend module is in scope. Browser
React review is forbidden for this workflow.

## Resilience and Duplicate-Work Requirements

- Baseline and issue snapshots carry the resolved `main` SHA and review ID.
- Each issue gets one canonical evidence record and one stable decision key:
  `issue-217-20260809:<issue-number>:<main-sha>`.
- Read-only audits may be repeated, but they write a new attempt record or
  compare checksums; they must not overwrite the authoritative decision.
- External issue mutations are not retried after an ambiguous response. The
  operator re-reads the remote state and routes the result to `BLOCKED` or
  `CONFLICT_REQUIRES_REVIEW`.
- Partial issue reviews remain `INCOMPLETE` or `BLOCKED`; they cannot be
  summarized as `COMPLETED` or `SUPERSEDED`.
- Missing SonarCloud access is recorded as `unverified`, never as a pass.

## Ordered Slices

### Slice 01 — Freeze baseline and verify requirement matrix

Purpose: capture current `main`, issue snapshots, comments, source provenance,
the complete requirement matrix and the no-action-yet guard.

```yaml
slice_id: S217-01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-217-obsolescence-review/requirement_matrix.md, .tiny-swarm/evidence/issue-217-obsolescence-review/baseline.md, .tiny-swarm/evidence/issue-217-obsolescence-review/issue-snapshots.md]
affected_modules: [requirements governance, GitHub issue snapshots, main baseline]
affected_contracts: [issue-217 requirement matrix, current-main provenance, no-action-yet guard]
dependencies: []
parallel_group: SERIAL-BASELINE
file_locks: [.tiny-swarm/evidence/issue-217-obsolescence-review/**]
contract_locks: [issue-217-decision-enum, issue-217-baseline-identity]
architecture_locks: [read-only-review-boundary]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: reviewed; no architecture change is authorized
  adr: none
stop_conditions: [dirty or unclear branch, missing current-main SHA, incomplete requirement matrix, issue snapshot drift before baseline, any close/rewrite attempt before evidence]
```

Done criteria: the matrix covers every explicit/implicit issue requirement;
all four issue snapshots and the baseline SHA are recorded; the current issue
states are confirmed open; no issue mutation occurred.

### Slice 02 — Audit Issue #156: central published-port requirement

Purpose: determine whether #156 is `COMPLETED`, `SUPERSEDED`, `REDUCE_SCOPE`,
`KEEP_OPEN` or `BLOCKED` from current source, tests, evidence and docs.

```yaml
slice_id: S217-02
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-217-obsolescence-review/issue-156-review.md, .tiny-swarm/evidence/issue-217-obsolescence-review/issue-156-test-results.md]
affected_modules: [infra/config/ports.yaml, infra/config/services.yml, infra/config/compose, deployment services, host integration, effective access model, Compose repository]
affected_contracts: [central published-port model, image-specific internal targets, effective URL/health-check model, safe published-port evidence]
dependencies: [S217-01]
parallel_group: P217-CANDIDATE-AUDITS
file_locks: [.tiny-swarm/evidence/issue-217-obsolescence-review/issue-156-*.md]
contract_locks: [issue-156-current-state-decision]
architecture_locks: [deployment-port-ownership]
quality_gates:
  targeted: [git diff --check, PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml, PYTHONPATH=src python3 -m unittest tests.integration.test_optional_service_routing]
  required: []
documentation:
  arc42: review port/effective-access sections; update only if verified architectural drift exists
  adr: review existing service-access and port ownership ADR references; do not create an ADR from the audit
stop_conditions: [untraced published-port producer, internal/external port ambiguity, missing safe evidence, unavailable required local test, live deployment required]
```

Done criteria: all five #156 checks are mapped to current files and named
verification; each requirement is `VERIFIED_LOCAL`, `UNVERIFIED` or
`BLOCKED`; one allowed decision and one recommended action are recorded.

### Slice 03 — Audit Issue #163: Sonar IP-literal findings

Purpose: determine the current state of the consolidated Sonar/test-fixture
requirement without changing runtime configuration.

```yaml
slice_id: S217-03
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Python Automation Developer]
affected_files: [.tiny-swarm/evidence/issue-217-obsolescence-review/issue-163-review.md, .tiny-swarm/evidence/issue-217-obsolescence-review/issue-163-test-results.md]
affected_modules: [tests/domain/network/test_port_forwarding_plan.py, tests/support/sonar_safe_literals.py, SonarCloud issue references]
affected_contracts: [test-fixture readability, S1313 finding state, Linux/WSL test baseline]
dependencies: [S217-01]
parallel_group: P217-CANDIDATE-AUDITS
file_locks: [.tiny-swarm/evidence/issue-217-obsolescence-review/issue-163-*.md]
contract_locks: [issue-163-current-state-decision]
architecture_locks: [test-only-no-runtime-change]
quality_gates:
  targeted: [git diff --check, PYTHONPATH=src python3 -m unittest tests.domain.network.test_port_forwarding_plan, rg -n "192\\.168\\.1\\.10|10\\.0\\.0\\.5" tests/domain/network/test_port_forwarding_plan.py]
  required: []
documentation:
  arc42: not applicable unless the audit discovers an architecture-level quality-policy drift
  adr: none
stop_conditions: [Sonar status claimed without observable external evidence, unreadable test intent, runtime configuration impact, unavailable targeted test]
```

Done criteria: each original finding is traced to current source or justified;
targeted test output and external Sonar state are recorded separately; one
allowed decision and recommended action are recorded.

### Slice 04 — Audit Issue #197: WSL Socat extraction

Purpose: determine whether the Socat behavior was extracted or remains a
composition-boundary residual, while preserving live-safety semantics as an
evidence requirement only.

```yaml
slice_id: S217-04
profile: FULL_PATH
owner: Senior System Architect
secondary_reviewers: [Senior Python Automation Developer, Senior Requirement Engineer, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-217-obsolescence-review/issue-197-review.md, .tiny-swarm/evidence/issue-217-obsolescence-review/issue-197-test-results.md]
affected_modules: [infrastructure/composition.py, infrastructure adapters, platform expose workflow, Socat manager, composition tests]
affected_contracts: [composition-root ownership, infrastructure-only process management, LiveConsent fail-closed guard]
dependencies: [S217-01]
parallel_group: P217-CANDIDATE-AUDITS
file_locks: [.tiny-swarm/evidence/issue-217-obsolescence-review/issue-197-*.md]
contract_locks: [issue-197-current-state-decision, composition-root-ownership]
architecture_locks: [hexagonal-infrastructure-boundary, live-consent-safety]
quality_gates:
  targeted: [git diff --check, PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition, rg -n "_WslSocat|wsl_socat|create_subprocess|socat" src/tiny_swarm_world/infrastructure/composition.py]
  required: []
documentation:
  arc42: review building-block/runtime responsibility sections; update only for verified drift
  adr: review existing composition and safety ADR references; no new ADR from an issue audit alone
stop_conditions: [composition ownership cannot be verified, consent/fail-closed behavior not observable in tests, live Socat required, architecture conflict]
```

Done criteria: all six #197 behavior cases are mapped to test evidence; source
ownership and consent behavior are explicit; one allowed decision and one
recommended action are recorded without moving code.

### Slice 05 — Consolidate Three-Amigos decisions and completion evidence

Purpose: reconcile the three disjoint audits, validate the allowed decision
enum, record duplicate/supersession relationships and produce the canonical
decision package before any issue action.

```yaml
slice_id: S217-05
profile: FULL_PATH
owner: Senior Workflow Architect
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Tester, Senior Documentation Engineer]
affected_files: [.tiny-swarm/evidence/issue-217-obsolescence-review/three-amigos.md, .tiny-swarm/evidence/issue-217-obsolescence-review/decision-record.md, .tiny-swarm/evidence/issue-217-obsolescence-review/deduplication-guard.md, .tiny-swarm/evidence/issue-217-obsolescence-review/acceptance_checklist.md]
affected_modules: [issue-217 evidence package, workflow governance, issue decision consolidation]
affected_contracts: [decision enum, requirement-to-evidence traceability, duplicate-work guard]
dependencies: [S217-02, S217-03, S217-04]
parallel_group: SERIAL-CONSOLIDATION
file_locks: [.tiny-swarm/evidence/issue-217-obsolescence-review/three-amigos.md, .tiny-swarm/evidence/issue-217-obsolescence-review/decision-record.md, .tiny-swarm/evidence/issue-217-obsolescence-review/deduplication-guard.md, .tiny-swarm/evidence/issue-217-obsolescence-review/acceptance_checklist.md]
contract_locks: [issue-217-canonical-decision-record, issue-217-idempotent-action-key]
architecture_locks: [no-product-change, no-duplicate-work]
quality_gates:
  targeted: [git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: record reviewed/no-change status or a verified drift handoff
  adr: record no-ADR-needed status unless a separate architecture decision is explicitly required
stop_conditions: [any open or guessed requirement, conflicting candidate decisions, duplicate relationship omitted, failed required quality gate, evidence state is ambiguous or not explicitly classified]
```

Done criteria: the three role perspectives are independently recorded; every
matrix row maps to implementation/test/evidence status; each issue has exactly
one decision; a canonical action key and conflict policy exist; required issue
evidence files are complete except the action result files.

### Slice 06 — Apply guarded issue actions and final audit

Purpose: perform the recommended GitHub issue close/rewrite/retain actions only
after the consolidated evidence gate, then re-read all affected issues and
hand off to the Issue Completion Auditor.

```yaml
slice_id: S217-06
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior System Architect, Senior Tester, Senior Documentation Engineer]
affected_files: [.tiny-swarm/evidence/issue-217-obsolescence-review/implementation_summary.md, .tiny-swarm/evidence/issue-217-obsolescence-review/changed_files.md, .tiny-swarm/evidence/issue-217-obsolescence-review/test_results.md, .tiny-swarm/evidence/issue-217-obsolescence-review/remaining_risks.md, .tiny-swarm/evidence/issue-217-obsolescence-review/issue-actions.md]
affected_modules: [GitHub issue state, issue bodies, issue comments, final evidence package]
affected_contracts: [issue action compare-and-set, close reason, reduced-scope rewrite, stale-evidence removal]
dependencies: [S217-05]
parallel_group: SERIAL-EXTERNAL-ACTIONS
file_locks: [.tiny-swarm/evidence/issue-217-obsolescence-review/implementation_summary.md, .tiny-swarm/evidence/issue-217-obsolescence-review/changed_files.md, .tiny-swarm/evidence/issue-217-obsolescence-review/test_results.md, .tiny-swarm/evidence/issue-217-obsolescence-review/remaining_risks.md, .tiny-swarm/evidence/issue-217-obsolescence-review/issue-actions.md]
contract_locks: [GitHub-issue-state, issue-217-action-key]
architecture_locks: [no-product-change, external-coordination-serialization]
quality_gates:
  targeted: [git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: final reviewed/no-change status; synchronize only verified architecture drift
  adr: none unless a separately approved decision is required
stop_conditions: [missing explicit workflow execution authorization for issue mutation, remote issue changed after S217-05, ambiguous mutation response, duplicate action key, any open/unverified requirement, failed quality gate]
```

Done criteria: every action is re-read-before-write, applied at most once,
post-state is re-read, and the action result is recorded. If mutation authority
or a remote precondition is missing, the slice ends `BLOCKED` with the
recommended action preserved and no partial close/rewrite claim.

## Dependency Graph

```text
S217-01
  |\
  | +--> S217-02 --\
  | +--> S217-03 ----> S217-05 --> S217-06
  | +--> S217-04 --/
```

Slices S217-02, S217-03 and S217-04 have disjoint evidence files and may run
in parallel in isolated worktrees after S217-01. Consolidation and all external
issue actions are serialized.

## Parallel Execution

- Can this workflow run in parallel? Partially: only S217-02 through S217-04.
- Conflicting workflows: any workflow that closes, rewrites or materially
  changes Issues #156, #163, #197 or their duplicate/supersession parents;
  any workflow changing the inspected port, composition or test surfaces.
- Shared files: the requirement matrix, final decision record, final evidence
  package, workflow governance files and GitHub issue state.
- Shared infrastructure: GitHub issue state is shared; local source inspection
  is read-only; live infrastructure is not used.
- Requires isolated worktree: yes for every executable slice; mandatory for the
  three parallel candidate audits.
- Requires serialized live validation: not applicable by default; any approved
  live/external validation remains serialized.
- Merge-order constraints: S217-01 first; S217-02/03/04 may converge only at
  S217-05; S217-06 is last and must re-read remote state.

## Automatic Work Distribution Policy

`workflow execute` must automatically analyze each slice for safe specialist
stream decomposition across backend, frontend, tests, runtime, documentation,
quality, architecture and security. It uses real Codex subagents where
supported; otherwise it performs explicit role-based fallback review in the
main execution thread. Before implementation or external action it must create
`.codex/evidence/slice-<number>-distribution.md`; for every implemented slice
it must create `.codex/evidence/slice-<number>-consolidation.md`. Codex remains
the final integration owner.

Stream map:

- backend: read-only Python path tracing by Senior Python Automation Developer;
- frontend: not applicable; browser React is forbidden;
- tests: targeted unittest and quality evidence by Senior Tester;
- runtime: read-only deployment/compose/WSL behavior inspection by Senior DevOps
  when needed; no live mutation;
- documentation: workflow, arc42, issue-body and evidence synchronization by
  Senior Documentation Engineer;
- quality: `QUALITY.md` gates and external-state classification;
- architecture: composition, port ownership and hexagonal-boundary review by
  Senior System Architect;
- security: Sonar finding interpretation, redaction and external action safety
  by the security reviewer when evidence requires it.

Do not parallelize when files overlap, the architecture boundary is unclear,
requirements contradict, ordering is mandatory, shared migrations or schemas
are involved, generated files conflict, Three Amigos rejects safe parallelism,
secrets handling is unclear, or safety guards would be weakened.

## Git Worktree Execution Rule

Every slice requires an isolated worktree. Parallel streams use branches named:

```text
feature/workflow-review-obsolete-issues-20260809-slice-<number>-<stream>
```

Workers verify the workflow branch and locks before writing, stay within their
allowed evidence scope, do not merge directly, and do not run on `main`,
`master`, `develop` or another shared branch. Codex consolidates accepted
findings after evidence and checks pass.

## Role and Ownership Map

| Responsibility | Owner |
|---|---|
| Workflow creation and dependency ordering | Senior Workflow Architect |
| Requirement extraction and EPIC/traceability drift | Senior Requirement Engineer |
| Port/composition architecture review | Senior System Architect |
| Python source-path inspection | Senior Python Automation Developer |
| Targeted tests and quality evidence | Senior Tester |
| Arc42/workflow/evidence synchronization | Senior Documentation Engineer |
| External issue action safety and deduplication | Senior Requirement Engineer with Senior System Architect review |
| Final completion decision | Issue Completion Auditor, not the implementer alone |

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/issue-217-obsolescence-review/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-217-obsolescence-review/`.
- Required evidence files: `requirement_matrix.md`, `implementation_summary.md`, `changed_files.md`, `test_results.md`, `remaining_risks.md`, `acceptance_checklist.md`, `baseline.md`, `issue-snapshots.md`, `issue-156-review.md`, `issue-163-review.md`, `issue-197-review.md`, `three-amigos.md`, `decision-record.md`, `deduplication-guard.md` and `issue-actions.md`.
- Requirement Lead review: S217-01 and S217-05.
- System Architect Reviewer review: S217-02/S217-04 and S217-05.
- Test / Evidence Reviewer review: S217-03 and S217-05.
- Issue Completion Auditor review: required at S217-06 before any `DONE` claim.
- DONE blocking rule: any open, guessed, conflicting or unverified requirement
  forces `INCOMPLETE`, `BLOCKED` or `FAILED`; `EXTERNAL_GATE_UNAVAILABLE` and
  missing issue mutation evidence are never success states.

## Quality-Gate Expectations

The authoritative commands come from `QUALITY.md`:

- targeted Python tests listed in S217-02, S217-03 and S217-04;
- `python3 tools/quality_gate.py quality` in S217-05 and S217-06;
- `git diff --check` before each evidence commit and before publication.

The full quality gate is local evidence only. It does not imply live Docker,
LXC, Incus, Swarm, Selenium or Sonar success. SonarCloud is classified as
`APPLICABLE_EXTERNAL`; an inaccessible result is `EXTERNAL_GATE_UNAVAILABLE`
and the affected issue remains `BLOCKED` or `KEEP_OPEN` as appropriate.

## Documentation Synchronization

- `documentation/arc42/**` was reviewed for port ownership, composition
  responsibility, runtime safety and quality expectations. No architecture
  change is made by this review workflow.
- If the audit finds verified architecture drift, record it as a handoff and
  stop before inventing an ADR or changing product architecture.
- No EPIC update is made because no matching EPIC exists; the traceability gap
  is explicit in the matrix and decision record.

## Stop Conditions and Uncertainty Escalation

Stop and report when:

- the branch is detached, dirty or not the declared workflow branch;
- current `main` cannot be resolved or issue snapshots cannot be verified;
- the requirement matrix omits an issue criterion;
- source, test or evidence paths cannot be verified;
- a decision would rely on commit-message matching, stale issue text or
  inferred relationships;
- Sonar or another external result is unavailable but would be required to
  claim completion;
- remote issue state changes after the consolidation baseline;
- a GitHub mutation may already have succeeded but its result is ambiguous;
- architecture ownership, duplicate/supersession relationship or quality
  authority is unclear;
- continuing would require product implementation, live infrastructure or
  silent scope reduction.

Escalate requirement ambiguity to Senior Requirement Engineer, architecture
ambiguity to Senior System Architect, test/quality failures to Senior Tester,
and external mutation conflicts to the Workflow Executor/Root Architect path.
Do not retry an ambiguous non-idempotent issue action.

## Commit and Publication Plan

Workflow authoring produces governance/evidence artifacts only. After
`documentation/workflow/workflow.md`, the context pack, the requirement matrix
and arc42 review status pass `git diff --check`, stage only workflow-authoring
files and directly required requirement evidence, create one authoring commit,
and push only `HEAD` to:

```text
origin/feature/workflow-review-obsolete-issues-20260809
```

This is guarded workflow-create publication. It does not create or merge a PR,
delete branches, force-push or run `push auto`.

## Definition of Done

- The complete requirement matrix exists and is reviewed.
- All six slices have concrete owners, dependencies, locks, stop conditions,
  evidence paths and verification commands.
- Three candidate audits are disjoint and converge through one consolidation
  gate.
- Each issue has exactly one allowed decision with current evidence and a
  recommended action.
- Duplicate/supersession relationships and idempotent action rules are
  recorded.
- Issue actions are either post-state verified or explicitly `BLOCKED` without
  claiming success.
- Required issue evidence and issue-completion-auditor review exist before
  `DONE`.
- Local quality gates and external/live applicability states are reported using
  `QUALITY.md` and the verification-state policy.

## Handoff to workflow execute

`workflow execute` may begin only on the declared implementation branch after
S3/S3D validates the workflow, the requirement matrix and the disjoint locks.
It must execute S217-01 first, may run S217-02/03/04 in isolated worktrees,
must serialize S217-05, and may run S217-06 only after the consolidated evidence
gate. The executor must not infer issue state, close an issue, rewrite an issue
or claim completion without the corresponding evidence and post-action state.

## Arc42 Check Status

`documentation/arc42/**` was checked against the issue scope, current
composition/port ownership and existing safety decisions. No arc42 or ADR
update is required for workflow authoring alone. Any verified architecture
drift discovered during execution is a handoff/blocker, not an implicit
product change.
