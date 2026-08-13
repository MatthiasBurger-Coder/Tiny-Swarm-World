# Indexed Workflow: Public-Beta-Reifegrad und Live-Green-Path

Workflow family id: `workflow-public-beta-roadmap-20260812`

Authoring branch: `docs/workflow-public-beta-roadmap-20260812`

Status: `AUTHORED_INDEXED_NOT_ACTIVE`

This is an indexed multi-issue workflow. The completed Issue #249 workflow and
its existing root context pack remain preserved. `workflow execute` must not
guess an issue-local workflow from this index; an issue workflow must first be
explicitly promoted to the active location or the executor must be invoked with
an explicitly supported indexed path.

## Executive Summary

The requested route is dependency-driven and aims at a controlled Public Beta:

```text
#121 -> #122 -> #123 -> #128 -> #126 -> #150 -> #124 -> #125 -> #129
     -> Public-Beta-Green-Path -> #120 closure audit
```

The route deliberately puts evidence, QMS, ISMS, branch/CI governance and the
admin-surface security model before the final Traefik GUI feature. Traceability,
the live-evidence contract and documentation navigation follow after the
feature so they describe the stabilized product state.

## Requirement Clarification Gate

### Original request

Create a workflow for the supplied dependency- and Public-Beta-oriented order,
including #121, #122, #123, #128, #126, #150, #124, #125, #129, a real
Public-Beta live green path, and final closure/reassessment of #120.

### Interpreted intent

Author one governed, indexed workflow family for the existing GitHub issues and
make the Public-Beta Green-Path an explicit release gate. Do not implement the
issues, change GitHub settings, create an external issue, or execute live
infrastructure in this authoring turn.

### Change type

Multi-issue workflow authoring covering audit evidence, quality/security
governance, repository governance, a security-sensitive Traefik admin surface,
traceability, live-evidence design, documentation navigation, and a final
reassessment gate.

### Affected process strand

`issue -> requirement matrix -> indexed workflow -> one issue branch/worktree ->
local verification -> issue evidence -> independent completion audit`

### Affected architecture areas

- Documentation, audit, QMS, ISMS, traceability and release governance.
- Docker Swarm-first deployment and Traefik HTTPS ingress for #150.
- Existing hexagonal Python automation and its live-consent/evidence guards.
- Public-Beta acceptance and redacted live evidence.

### Explicit requirements

1. Preserve the requested execution order and dependency rationale.
2. Create one issue-local executable workflow and context pack for each of
   #121, #122, #123, #128, #126, #150, #124, #125, #129 and #120.
3. Keep #127 out of the new plan because it is already closed and its local
   supply-chain artifacts are present; record that prerequisite explicitly.
4. Represent the Public-Beta Green-Path as a blocked release gate until a
   concrete issue/workflow identity and explicit live-run consent exist.
5. Make all workflow slices requirement-matrix-, evidence-, quality-gate- and
   issue-completion-auditor-aware.
6. Preserve Linux/WSL-only, Docker Swarm-first, fail-closed, redaction and
   no-live-default rules.
7. Treat #150 as a security-sensitive feature whose route, authentication,
   authorization, TLS and exposure boundary are decided before implementation.

### Implicit requirements

- Indexed workflows must not overwrite the completed #249 workflow.
- Every executable slice needs concrete locks, dependencies, owner, done
  criteria, verification commands and stop conditions.
- Documentation status must distinguish implemented, planned, blocked,
  resource-gated, failed-to-apply and failed-to-verify states.
- #120 cannot be closed from documentation presence alone; it requires a fresh
  audit/reassessment on `main` after the child work and Green-Path evidence.
- #129's recommended #127 dependency is satisfied by the already closed issue,
  not silently omitted.

### Assumptions accepted from the request

- The linked GitHub issue bodies are the issue-level sources of truth.
- One authoring branch is used for this indexed plan; later execution creates
  issue-specific branches/worktrees in sequence.
- The Green-Path may be authored as a release gate without inventing a new
  issue number. It remains non-executable until refined.
- Native Linux and WSL2 are separate acceptance targets, and fresh install,
  reconcile/re-run and update are separate scenarios.

### Non-goals

- No production implementation in this workflow-authoring branch.
- No live Incus/LXC, Docker Engine, Swarm, networking, Traefik, stack,
  Portainer, Nexus, Jenkins, Pulsar, SonarQube, Swagger or Infisical commands.
- No direct GitHub branch-protection mutation, CI workflow creation, PR merge,
  certification claim or risk closure without evidence.
- No browser React project; browser/live checks remain explicitly gated.
- No reintroduction of Java, Maven, Spring Boot or Kubernetes-first behavior.

### Risks

- Governance documents can appear complete while runtime evidence remains
  missing; missing evidence is not a pass and status language must prevent false
  closure.
- #150 can accidentally expose an unauthenticated dashboard or duplicate the
  existing Service Access surface.
- The requested route is stricter than the issue dependency hints and may
  expose missing issue relationships during execution.
- A clean install alone can hide reconcile/update defects.

### Open questions and blockers

1. **Green-Path identity:** no concrete issue number, owner, exact live
   command contract, host prerequisites or evidence storage decision was
   supplied. This blocks the Green-Path gate and therefore blocks #120 closure.
2. **#150 route/auth choice:** the existing ADR and ASVS/ISMS slices must make
   the final admin-surface decision before implementation. This is a planned
   architecture decision gate, not an assumption that basic auth or a specific
   hostname is already approved.

### Confidence and decision

Confidence: `86%`.

Decision: `PROCEED_WITH_ACCEPTED_ASSUMPTIONS` for indexed workflow authoring.
The accepted assumptions are non-blocking for documenting the existing issue
workflows. They remain execution blockers for the Green-Path and #120 closure.

## Verified Baseline

- Repository baseline was a clean `main` worktree before branch creation.
- Current authoring branch: `docs/workflow-public-beta-roadmap-20260812`.
- Canonical local gates are defined by `QUALITY.md`; documentation-only
  authoring uses `git diff --check`, while implementation slices require the
  applicable Python quality gate.
- `documentation/workflow/workflow.md` is the completed #249 workflow and is
  preserved.
- #127 is closed on GitHub; `documentation/security/supply-chain-security.md`,
  `sbom-policy.md`, `dependency-scan-policy.md`,
  `container-image-scan-policy.md`, and `tools/security_gate.py` are present.
- The current Traefik ADR is
  `documentation/arc42/09_decisions/adr-traefik-https-ingress-existing-ca.adoc`.
  The older path mentioned by #150 is not the current canonical path.
- `infra/config/compose/traefik/docker-compose.yml` enables the dashboard but
  does not authorize insecure API exposure; domain and routing tests already
  enforce HTTPS-oriented route contracts.
- No live Green-Path evidence is inferred from static files or existing tests.

## Target Picture

```text
Audit evidence (#121)
        |
        v
QMS (#122) -> ISMS (#123) -> Branch/CI governance (#128)
        |                         |
        +----------> ASVS/admin-surface model (#126)
                                      |
                           Secure Traefik GUI (#150)
                                      |
                         Traceability (#124) -> Live evidence contract (#125)
                                      |
                              Documentation navigation (#129)
                                      |
                 Public-Beta gate: Linux + WSL2, A/B/C, redacted evidence
                                      |
                         Re-audit and close roadmap #120
```

## Ordered Issue Workflows

| Order | Issue / gate | Workflow path | Dependencies | Status |
|---:|---|---|---|---|
| 01 | #121 Audit Evidence Structure | `issues/issue-121/workflow.md` | none | completed |
| 02 | #122 QMS-light | `issues/issue-122/workflow.md` | #121 | completed |
| 03 | #123 ISMS-light | `issues/issue-123/workflow.md` | #121; #122 | completed |
| 04 | #128 Branch Protection / CI Governance | `issues/issue-128/workflow.md` | #121; #122; #123 | completed |
| 05 | #126 OWASP ASVS / Admin Surface | `issues/issue-126/workflow.md` | #121; #123; #128 governance context | completed |
| 06 | #150 Secure Traefik GUI | `issues/issue-150/workflow.md` | #123; #126; #128 | blocked: local complete; live consent pending |
| 07 | #124 Traceability Matrix | `issues/issue-124/workflow.md` | #121; all stabilized implementation context | blocked: local complete; live/external rows open |
| 08 | #125 Live Evidence Contract | `issues/issue-125/workflow.md` | #121; #124; #150 | in progress |
| 09 | #129 Documentation Navigation | `issues/issue-129/workflow.md` | #121-#126; #128; #150; #124; #125; #127 already closed | authored |
| 10 | Public-Beta Green-Path gate | no issue-local workflow yet | #125; #129; explicit live consent | **BLOCKED / refinement required** |
| 11 | #120 Roadmap closure and re-audit | `issues/issue-120/workflow.md` | all above, including Green-Path PASS | authored; execution blocked by gate |

## Dependency Graph

```text
I121 -> I122 -> I123 -> I128 -> I126 -> I150 -> I124 -> I125 -> I129
                                                                    |
                                                                    v
                                                        GATE-PUBLIC-BETA
                                                                    |
                                                                    v
                                                                  I120
```

`I127` is a closed prerequisite already represented by repository supply-chain
artifacts. It is not a missing edge in the graph. If the execution audit finds
those artifacts inconsistent with the closed issue, stop and reopen the
dependency decision rather than silently proceeding.

## Three-Amigos Gate and Ownership

| Perspective | Required role | Decision for this index |
|---|---|---|
| Requirement | Senior Requirement Engineer | requirements extracted; Green-Path identity remains a blocker |
| Architecture | Senior System Architect | sequence fits current hexagonal/Docker Swarm architecture; #150 ADR gate required |
| Python automation | Senior Python Automation Developer | no Python implementation in authoring; #150 and Green-Path must preserve ports/adapters and consent guards |
| Test / evidence | Senior Tester | local gates and evidence packages are explicit; live states cannot be inferred |
| Audit evidence | Audit Evidence Manager | required for #121/#120 and cross-issue status language |
| Security | ISMS/ASVS/Security Threat Modeling | required for #123/#126/#150 and all secret/admin-surface decisions |
| Documentation | Documentation Sync / Audience Architect | required for #129 and arc42 synchronization |
| Live acceptance | Live Evidence Validation / Acceptance Checks | required for the blocked Green-Path gate |

## Cross-Workflow Execution Rules

### Parallel Execution

- Can this workflow family run in parallel? **No for implementation.** The
  requested sequence is dependency-ordered and governance artifacts are shared.
- Read-only role reviews may run in parallel inside an issue slice when locks
  are disjoint.
- Conflicting workflows: any workflow changing audit, QMS, ISMS, security,
  branch policy, Traefik routing, traceability, live evidence or documentation
  navigation outside this family.
- Shared files: `AGENTS.md`, `QUALITY.md`, arc42, `documentation/README.adoc`,
  audit/security/governance indexes, and issue evidence references.
- Every executable issue workflow requires its own isolated Git worktree.
- Live validation is serialized; no shared live environment is assumed.
- Merge order follows the table above. No child workflow is promoted over an
  unresolved predecessor.

### Automatic Work Distribution Policy

`workflow execute` must analyze every slice for safe specialist streams across
backend, frontend, tests, runtime, documentation, quality, architecture and
security. It must use real Codex subagents where supported and perform an
explicit role-based fallback review when they are unavailable. Before
implementation it must create `.codex/evidence/slice-<number>-distribution.md`;
after each implemented slice it must create
`.codex/evidence/slice-<number>-consolidation.md`. Codex remains final
integration owner.

Stream map: documentation/audit -> Documentation Engineer and audit manager;
Python/runtime -> Senior Python Automation Developer and DevOps; tests/quality
-> Senior Tester and quality-gate owner; architecture -> Senior System
Architect; security -> ISMS/ASVS/Threat Modeling; live acceptance -> Live
Evidence Validation and Acceptance Checks; frontend -> not applicable unless a
verified real frontend module appears.

Do not parallelize overlapping files, unclear architecture, contradictory
requirements, mandatory ordering, shared migrations, generated-file conflicts,
unclear secrets handling, weakened safety guards, or a Three-Amigos
not-safely-parallelizable decision.

### Git Worktree Execution Rule

Each issue execution requires an isolated worktree and an issue branch derived
from the explicit issue workflow. Workers must verify the workflow branch and
locks before writing, remain within the declared scope and never merge directly
to the integration branch. The authoring branch is not an implementation
worktree. Live validation requires a separately approved serialized worktree or
operator run and its own evidence package.

## Issue Completion Discipline

Every issue workflow defines a requirement matrix at
`.tiny-swarm/evidence/issue-<id>/requirement_matrix.md` and required evidence
files beside it:

- `implementation_summary.md`
- `changed_files.md`
- `test_results.md`
- `remaining_risks.md`
- `acceptance_checklist.md`

Every requirement must map to implementation/config/documentation evidence and
verification evidence. The Requirement Lead, System Architect Reviewer, Test /
Evidence Reviewer and Issue Completion Auditor must all review before `DONE`.
Open or unverified requirements force `INCOMPLETE`, `BLOCKED` or `FAILED`.

## Quality and Evidence Policy

Authoritative local commands come from `QUALITY.md`:

```bash
git diff --check
python3 tools/quality_gate.py quality
```

Use targeted gates first for implementation slices. The full Python gate is
local evidence only. Live, browser and external quality states must use the
canonical verification-state policy and may not be reported as passed without
executed evidence. No default gate may run Incus/LXC, Docker Swarm, compose,
stack bootstrap, networking or service commands.

## Scope

The indexed scope is workflow authoring for the ten existing issues, their
dependency order, evidence contracts and the final release gate. Product
implementation happens only in later issue-specific executions.

## Target Outcome

The intended outcome is a documented, reviewable and evidence-honest path to
Public Beta, with #120 closed only after a fresh audit on `main`. Until the
Green-Path gate is refined and passed, the outcome is intentionally not
achieved.

## Architecture Constraints

Preserve hexagonal boundaries, Docker Swarm-first/LXC-Incus provider direction,
explicit live consent, fail-closed behavior, redaction, existing Traefik HTTPS
decisions and the distinction between desired state, local tests and observed
runtime evidence. No new service boundary is implied by these workflows.

## Python Automation Assessment

Most indexed issues are documentation/governance-only. #150 and the later
Green-Path can affect Python orchestration, ports, adapters, provider runtime
and evidence handling; those slices explicitly require Senior Python
Automation Developer review, deterministic tests and WSL/Linux verification.

## Frontend Assessment

No browser React project is in scope. #150 is a Traefik administrative surface,
not a new frontend. Browser/live verification is conditional and must use the
existing live-evidence contract after explicit consent.

## Test Strategy

Documentation slices use path/reference validation and `git diff --check`.
Executable #150 slices use focused domain/compose/routing tests followed by
`python3 tools/quality_gate.py quality`. The final gate reviews redacted live
evidence for native Linux and WSL2, fresh/re-run/update, readiness and second
run behavior; static tests never substitute for that evidence.

## Resilience Requirements

All workflows preserve explicit retry/reconcile/update, cleanup, rollback,
blocked/refused/resource-gated/failed-to-apply/failed-to-verify states and
redaction. Governance closure requires effectiveness evidence. The Green-Path
must prove re-run and update, not only fresh install.

## Role or Subagent Ownership Map

Senior Requirement Engineer owns matrices and drift; Senior System Architect
owns boundaries/ADRs; Senior Python Automation Developer owns any executable
automation; Senior Tester owns tests/evidence; Documentation Engineer owns
navigation/arc42; Audit/QMS/ISMS/ASVS/Live Evidence specialists own their
governance contracts; Issue Completion Auditor owns final status.

## Commit and Push Plan

This authoring branch publishes only the indexed workflow artifacts through one
guarded workflow-authoring commit and a push to
`origin/docs/workflow-public-beta-roadmap-20260812`. It must not create, merge
or clean up a PR. Later issue execution uses one issue-scoped commit per slice
and the normal guarded workflow process.

## Public-Beta Gate Contract (not executable yet)

The gate must eventually prove, with explicit consent and redacted evidence:

1. Native Linux: fresh install, reconcile/re-run, update.
2. WSL2: fresh install, reconcile/re-run, update.
3. Preflight, Incus/LXC nodes, Docker Engine, Swarm, network/Traefik,
   Infisical/secrets, Nexus/artifacts, Jenkins, SonarQube, Pulsar, Swagger and
   service access readiness.
4. Browser/readiness verification where applicable.
5. Evidence bundle, checksums, redaction report and reviewer decision.
6. A second successful run after the first run, with drift/reconcile evidence.

The gate is not a pass when it is refused, blocked, resource-gated,
failed-to-apply or failed-to-verify. It cannot be executed from this authoring
branch. A concrete issue/workflow identity, host matrix, command contract,
reset/update semantics, evidence root, operator/consent record and rollback
plan must be supplied before execution.

## Handoff and Promotion

1. Review this index and select exactly one issue path.
2. Promote that issue workflow to the active workflow location or extend the
   executor explicitly to accept its indexed path.
3. Run S3/S3D preflight, verify branch/worktree/locks and create the requirement
   matrix before implementation.
4. Execute only the selected issue and its declared dependencies.
5. Do not execute the Green-Path or close #120 until the gate is refined and
   independently reviewed.

## Arc42 Check Status

Relevant arc42 context, constraints, building blocks, runtime, deployment,
quality, risks and Traefik decision files were reviewed. No arc42 change is
claimed by this workflow-authoring turn; later implementation slices update only
verified behavior.

## Definition of Done for This Authoring Turn

- The index records the requested order, dependencies, assumptions, blockers,
  role ownership, safety rules and execution handoff.
- All ten existing issue workflows have complete issue-local workflow and
  context-pack artifacts.
- #127 is explicitly accounted for as closed, not silently skipped.
- The Green-Path is explicitly blocked rather than represented as verified.
- Existing #249 workflow artifacts remain untouched.
- `git diff --check` passes before publication.

## Authoring Verification Evidence

- `git diff --cached --check`: `PASS`.
- `python3 tools/check_verification_policy_consistency.py` in WSL: `PASS`.
- `python3 tools/quality_gate.py quality` in WSL: `NOT COMPLETED`; the
  documentation-only authoring run exceeded the 120-second command window.
  This is not reported as a quality pass. The issue workflows retain the
  authoritative full-gate requirement for any executable implementation slice.
- Live, browser and external verification: `LIVE_NOT_APPLICABLE` for this
  authoring turn; no live command was executed.

## Source Issues

- [#120 roadmap](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/120)
- [#121 audit evidence](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/121)
- [#122 QMS-light](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/122)
- [#123 ISMS-light](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/123)
- [#124 traceability](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/124)
- [#125 live evidence contract](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/125)
- [#126 OWASP ASVS](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/126)
- [#127 supply-chain gate, already closed](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/127)
- [#128 branch/CI governance](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/128)
- [#129 documentation navigation](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/129)
- [#150 secure Traefik GUI](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/150)
