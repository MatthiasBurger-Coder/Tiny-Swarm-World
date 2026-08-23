# Workflow: Issue #252 — Classic Profile Stabilization / Public Beta RC1

Workflow id: issue-252-classic-public-beta-rc1-remediation-20260823

Source issue: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/252

Execution profile: FULL_PATH

Authoring branch: feature/workflow-issue-252-remediation-20260823

Planned execution branch: feature/classic-public-beta-rc1-stabilization

Status: REMEDIATION_AUTHORED_NOT_EXECUTED

No live installation, infrastructure mutation, browser check, credential test,
release claim or RC1_ACCEPTED decision is produced by workflow authoring.

## Executive Summary

Issue #252 qualifies the current Classic profile for Public Beta RC1 through a
repeatable, evidence-backed lifecycle on current main:

~~~text
Fresh Install
  -> Post-install acceptance
  -> Re-run/Reconcile
  -> Post-reconcile acceptance
  -> Update
  -> Post-update acceptance
  -> Failure/Recovery
  -> CI/External-Gate qualification
  -> RC1 decision
~~~

The supported reference path remains:

~~~text
Linux / WSL2
  -> managed Incus/LXC
      -> manager + workers
          -> Docker Engine
              -> Docker Swarm
                  -> routing -> secrets -> artifacts -> services
~~~

This is release qualification, not a new runtime implementation. Assertion-
heavy acceptance tests stay under tests/, the existing post-install browser
test is reused or migrated without duplication, and native Linux and WSL2
remain separate evidence targets.

Issue #252 now includes a mandatory CI/release-gate addendum. The required
automation path is:

~~~text
PR/Push Python quality gate
  -> Conda compatibility matrix
  -> Sonar workflow reconciliation
  -> scheduled/dispatchable Classic live workflow
  -> real workflow-run and failure-semantic evidence
~~~

The CI layer is part of this issue, not a follow-up. Standard hosted runners
must remain free of Incus, Docker, Swarm, service bootstrap and credentialed
live mutation. The Classic live workflow therefore requires a verified,
dedicated self-hosted runner strategy or must remain explicitly blocked.

The requested administrator-PowerShell access is not a repository workflow
capability and cannot be granted by this workflow. Project Python, test and
quality commands remain Linux/WSL commands. A live operator must independently
possess required permissions on the explicitly selected target; missing
permissions are a prerequisite blocker, never authorization inferred by this
workflow.

## Requirement Clarification Gate

### Original request

Create or extend the workflow for GitHub Issue #252, including the mandatory
CI/release-gate addendum, with full access including an administrator
PowerShell console.

### Interpreted intent

Author an executable, governance-compliant RC1 stabilization workflow for the
Classic profile. It covers the complete lifecycle, the mandatory CI workflows,
real workflow-run evidence, runner qualification, current tool/test inventory,
canonical test ownership, explicit WSL2 and native-Linux qualification,
redacted evidence and the final RC1 decision from observed results.

The PowerShell request is treated as an operator-environment request. It does
not authorize privilege escalation, change the repository Linux/WSL-only model,
or permit project commands through Windows Python or PowerShell path invocation.

### Change type

Release-qualification workflow with Python test/harness impact, live runtime
validation, platform/deployment evidence, recovery checks, security-sensitive
redaction, and release-governance consequences.

### Affected process strand

issue -> requirement matrix -> Three-Amigos decision -> asset inventory ->
deterministic acceptance coverage -> local gates -> explicit live consent ->
host/scenario evidence -> defect classification -> independent completion audit
-> RC1 decision

### Affected architecture area

- Linux/WSL2 host classification and filesystem policy.
- Managed Incus/LXC provider, manager/worker lifecycle and Docker readiness.
- Docker Swarm bootstrap, routing, Service Access, secrets and artifacts.
- Jenkins, Nexus, SonarQube, Pulsar, Swagger/OpenAPI and other current
  Classic-profile services.
- Existing Python hexagonal boundaries, workflow guards, reconcile/update
  behavior and local evidence repositories.
- tools/ diagnostics/runners versus assertion-heavy tests under tests/.
- Live/browser evidence contract and Public Beta release decision.
- GitHub Actions quality, compatibility, SonarCloud and Classic-live runner
  qualification.

### Explicit requirements

1. Qualify the current Classic profile as Public Beta RC1 only through repeatable
   observed lifecycle evidence on current main.
2. Preserve the Linux/WSL2 -> Incus/LXC -> Docker Engine -> Docker Swarm path;
   Podman, Kubernetes and new orchestration abstractions are out of scope.
3. Execute and evidence Fresh Install, post-install acceptance,
   Re-run/Reconcile, post-reconcile acceptance, Update, post-update acceptance,
   Failure/Recovery and the final RC1 decision.
4. Keep executable utilities, diagnostics, recovery helpers and optional runners
   in tools/; keep assertion-heavy acceptance tests under tests/.
5. Inventory named tools/tests and classify every asset as REUSE_AS_IS,
   EXTEND, MOVE_TO_TESTS, WRAP_IN_RC1_SCENARIO, REPLACE_WITH_REASON or
   NOT_APPLICABLE.
6. Reuse or migrate tests/integration/test_post_install_browser_live.py and
   do not create a duplicate live-test framework.
7. Create the Three-Amigos decision before live execution, including
   environments, scenarios, required services, state transitions, evidence,
   timeouts, stop conditions, defect severity and release decision.
8. Derive the authoritative current Classic service list from current
   configuration and classify every service RC1_REQUIRED, RC1_OPTIONAL or
   NOT_IN_CLASSIC_PROFILE.
9. Make required service, routing, secret, artifact, readiness, idempotence,
   update, failure and recovery checks observable and redaction-safe.
10. Do not treat blocked, degraded, partial, skipped, failed-to-apply or
    failed-to-verify scenarios as RC1 success.
11. Require complete redacted evidence and exactly one final decision:
    RC1_ACCEPTED, RC1_REJECTED_BLOCKERS or RC1_REJECTED_EVIDENCE_INCOMPLETE.
12. Provide `python-quality-gate.yml` for PR and push quality validation using
    the locked repository gate and fail-closed result reporting.
13. Provide `python-compatibility.yml` with the supported Conda Python matrix;
    the initial matrix is Python 3.12 and 3.13, subject to implementation-time
    verification against the supported package/runtime contract.
14. Reconcile `sonar_check.yml` as the external SonarCloud gate without
    duplicating or weakening the canonical Python quality gate. Missing or
    unavailable Sonar status is not green evidence.
15. Provide `nightly-classic-live.yml` with schedule and manual dispatch,
    explicit environment/consent gates, redacted evidence publication and a
    verified self-hosted Classic-capable runner strategy.
16. Execute real CI workflow runs and prove failure semantics: failed,
    skipped, blocked, unauthorized, unavailable or unverified required gates
    must not aggregate to RC1 success.

### Implicit requirements

- Current main is the baseline; authoring and implementation use dedicated
  branches/worktrees and never write to main.
- Native Linux and WSL2 evidence are separate; one host cannot substitute for
  the other.
- A second run proves idempotence and absence of unintended destruction.
- Update proves convergence while preserving unrelated healthy state.
- Live phases stop dependents after a failed or unverifiable phase.
- Raw secrets, tokens, credentials, full environment files, authorization
  headers, private keys and unredacted host output never enter evidence.
- LIVE_VERIFIED requires authorized execution plus complete redacted evidence.
- Every blocker/major defect gets smallest-root-cause handling and regression
  coverage; there is no blocker waiver.
- Exact reconcile/update commands and one reversible update change are selected
  by the Three-Amigos decision from current behavior, not guessed here.
- Administrative host access is an external prerequisite, not granted by a
  workflow document.
- A repository/org administrator can provide or approve a self-hosted runner
  with documented labels and access to the selected Classic live target; its
  availability is an execution prerequisite, not an inferred capability.
- Conda can resolve the supported Python matrix against the locked runtime and
  development requirements without changing the product's Linux/WSL model.
- GitHub Actions status, artifacts and SonarCloud status are externally
  observable for the final audit.

### Assumptions

- The GitHub Issue #252 body is the requirement source because no local EPIC
  directly owns Classic RC1 qualification.
- Current service membership is derived from current main configuration in
  S252-01.
- tests/live/test_post_install_browser_live.py and
  tests/integration/test_post_install_browser_live.py are candidate assets;
  S252-01/S252-02 decide which is canonical.
- Existing live-run and green-path evidence contracts are reusable and remain
  planned contracts until an authorized run produces evidence.
- A disposable or recoverable target can be provided for each host class.

### Non-goals

- No Podman, Kubernetes, alternate runtime, new orchestration abstraction,
  microservice extraction or broad refactor.
- No Java, Maven, Spring Boot or Windows-native project behavior.
- No administrator PowerShell privilege escalation or PowerShell project
  execution.
- No live commands during authoring.
- No automatic host package installation, daemon repair, firewall/bridge change,
  broad mount, privileged-profile change or silent reset.
- No duplicate live-test framework or silent reduction of the scenario matrix.
- No RC1 claim from static tests, planned commands, configuration or skipped
  scenarios.
- No raw secret/token/password/join-token or unredacted evidence storage.
- No GitHub branch-protection mutation, PR merge, release tag or public-beta
  claim during workflow authoring.

### Risks

- Current service membership or canonical commands may differ from historical
  docs; S252-01 derives them from current configuration.
- Live failures can leave partial state; ownership-safe cleanup and evidence
  are mandatory.
- WSL2 and native Linux can diverge in Incus, systemd, filesystem, networking
  or resource behavior.
- Fresh install can conceal reconcile, update, restart or recovery defects.
- Browser/API checks can leak credentials unless summaries are redacted first.
- Existing integration/live suites may overlap; duplication is a stop condition.
- A branch or local quality pass is not live or external release evidence.
- A GitHub-hosted runner cannot satisfy the Classic live environment merely by
  installing Python; missing self-hosted capability is a blocker.
- CI workflows can pass their own YAML/static checks while never having run a
  real scheduled/manual workflow; execution evidence is mandatory.

### Open questions and execution blockers

S252-01 must decide: current required/optional service membership; canonical
test location; exact supported reconcile command; exact reversible update
change; browser/API checks; target ownership, prerequisites and resource
contracts; exact CI matrix package/install contract; self-hosted runner labels
and target ownership; Sonar responsibility and required external status.
These are not authoring blockers when recorded as executable prerequisites, but
execution cannot continue while any remains unresolved.

Execution also stops for missing explicit live consent, missing host access or
permissions, failed preflight, unsafe filesystem, missing credentials/reference,
missing redaction/evidence path, unclear recovery ownership, or any architecture
decision that would require bypassing fail-closed guards.

### Confidence and decision

Confidence: 92 percent.

Decision: READY_FOR_WORKFLOW.

The issue supplies a detailed objective, lifecycle, scenario list, non-goals and
acceptance criteria. Remaining facts are intentionally derived from current
repository behavior in the first execution slice and are not silently treated
as implemented or live-verified.

### Remediation clarification — 2026-08-23

- Original request: adopt the updated TLS ADR, add the possible RC1 fixes, and
  authorize a remediation workflow or scope extension with separate slices.
- Interpreted intent: preserve Issue #252 Classic RC1 scope while repairing
  defects discovered by WSL2 live stabilization before repeating dependent
  host and external gates.
- Accepted assumption source: the user's explicit instructions immediately
  after remote ADR synchronization.
- EPIC fit question: yes; the requested implementation still matches Issue
  #252 and its accepted managed-or-operator CA decision.
- Non-goals: Kubernetes, Podman, new PKI service, implicit trust-store/sysctl/
  firewall mutation, broad composition refactoring, stale-evidence promotion,
  or RC1 acceptance without Native Linux and external-gate evidence.
- Decision: `READY_FOR_WORKFLOW` with 95 percent confidence after the separate
  remediation scopes, locks, dependencies, acceptance checks and stop paths
  below are applied.
- Five-role gate: Senior Requirement Engineer, Senior System Architect, Senior
  Python Automation Developer, Senior Tester, and Senior Workflow Architect as
  dependency/deadlock validator. The fifth role validates the complete DAG,
  file/contract locks and serialized merge order; it does not replace any of
  the four implementation perspectives.

## Target Picture

~~~text
Current main + verified Classic config
          |
          v
Requirement matrix + service inventory + Three-Amigos decision
          |
          v
Canonical tests/tools with no duplication
          |
          v
Local quality + static/pre-live diagnostics
          |
          v
CI quality + compatibility + Sonar + Classic-live runner qualification
          |
          v
WSL2: fresh -> accept -> reconcile -> accept -> update -> accept
          |
          v
Native Linux: fresh -> accept -> reconcile -> accept -> update -> accept
          |
          v
Failure/recovery/restart + redacted evidence + defect regression
          |
          v
Independent audit -> RC1_ACCEPTED or explicit rejection
~~~

## Verified Baseline

- The remediation authoring worktree was created cleanly from execution-branch
  baseline `f02d14d3` (`origin/feature/classic-public-beta-rc1-stabilization`).
  This is not represented as the current `main` commit.
- QUALITY.md defines git diff --check and python3 tools/quality_gate.py quality.
- tools/install_debugger.py, tools/preflight.py, tools/quality_gate.py and
  tools/security_gate.py exist.
- An opt-in live browser suite exists at
  tests/live/test_post_install_browser_live.py and an integration suite exists
  at tests/integration/test_post_install_browser_live.py; their canonical
  relationship must be decided before adding coverage.
- documentation/evidence/live-run-template.md,
  documentation/evidence/live-greenpath-evidence-contract.md and the
  verification-state policy define redaction, checksums, exact live states and
  no-live-default semantics.
- Arc42 and ADRs confirm Linux/WSL2-only operation, managed Incus/LXC,
  Docker Swarm-first deployment, explicit live consent, fail-closed mutation,
  verify-after-apply behavior, hexagonal boundaries and ignored local evidence.
- Historical local workflow records exist for S252-01 through S252-03 and a
  redacted WSL2 recovery/post-install run exists for S252-04. They remain
  bounded evidence, not proof that the full issue lifecycle or CI addendum is
  complete.
- Historical tracked consolidation evidence reports WSL2 reconcile (S252-05),
  update (S252-06), and failure/recovery/restart work (S252-07). Those results
  remain historical evidence for their recorded SHAs and are not transferred
  to the new remediation candidate. Native-Linux, required self-hosted CI,
  external SonarCloud and final RC1 evidence remain open.

## Scope

In scope: the issue requirement matrix and Three-Amigos decision; current asset
inventory and service classification; canonical acceptance-test placement;
deterministic lifecycle/fail-closed/recovery tests; explicit WSL2 and native
Linux pre-live, fresh, reconcile, update, failure/recovery/restart and
service/browser/API runs; redacted scenario evidence; defect classification;
independent completion audit; final RC1 decision; Arc42/ADR consistency review;
PR/push quality, Conda compatibility, Sonar reconciliation, scheduled/manual
Classic-live automation and real CI-run evidence.

Product architecture changes occur only when verified behavior requires them and
only in the declared defect/fix scope. Workflow authoring itself does not
change product runtime behavior.

## Architecture Constraints

- Preserve domain -> application -> infrastructure direction.
- Keep command, filesystem, HTTP/browser, Docker, Incus, Swarm, YAML and
  credential details in infrastructure adapters or test support.
- Keep infrastructure wiring in src/tiny_swarm_world/infrastructure/composition.py
  and keep __main__.py thin.
- Preserve the lxc_native/Incus direction; no Multipass fallback.
- Preserve explicit --live --approve-live or approved interactive consent for
  non-interactive live mutation. Consent is per invocation and does not satisfy
  reset/destroy confirmation.
- Keep observed runtime evidence in ignored local state and serialize only
  allowlisted redacted summaries.
- Fail closed before mutation when host, filesystem, provider, credential,
  resource, ownership or verification contracts are absent.
- Verify after every mutating phase and stop dependents on failure.
- Do not use PowerShell as the project execution environment.

## Python Automation Assessment

Expected work is acceptance coverage and evidence orchestration, not a new
product service. Python changes must use existing ports/services/adapters, keep
live execution out of constructors/import-time effects, use asyncio for
asynchronous orchestration, use deterministic fixtures for local scenarios,
preserve timeout/retry/redaction/cleanup/verify-after-apply contracts, and add
focused tests before the full WSL/Linux quality gate.

## Frontend Assessment

No React or browser frontend implementation is authorized. Browser checks are
conditional acceptance checks against existing service/admin surfaces. The
Console/status UI reviewer is N/A for authoring because no terminal presentation
change is requested; it becomes required if a slice changes progress/status
output or terminal interaction.

## Test Strategy

S252-01 creates the stable matrix, service inventory and Three-Amigos decision
before implementation or live execution. S252-02 selects exactly one canonical
acceptance-test location. S252-03 covers deterministic prerequisite failure,
partial state, reconcile, update, restart classification and redaction. Live
checks use one approved host at a time, explicit consent, bounded retries,
redacted evidence and serialized mutation. Final audit maps every requirement
to implementation, verification and evidence.

## Resilience Requirements

Preflight is read-only and fail-closed. Apply phases are bounded, observable
and followed by verification. Retries are explicit and bounded; destructive
operations are not blindly retried. Reconcile reuses valid managed state,
avoids duplicate state and avoids unintended destruction. Update preserves
unrelated healthy state and retains rollback evidence. Ambiguous/corrupt state
stops before mutation. Failure after mutation remains
LIVE_FAILED_AFTER_MUTATION until repaired and re-verified.

## Service and Runtime Contract

S252-01 records one authoritative row for every configured Classic service:
service_id, profile membership, RC1 classification, owner/boundary,
endpoint/readiness contract, credential/reference requirement, evidence file,
timeout, failure severity and dependent scenarios.

At minimum review Service Access/routing, Infisical/secrets, Nexus/artifacts,
Jenkins, SonarQube, Apache Pulsar/Pulsar Manager when configured,
Swagger/OpenAPI, Portainer and every additional selected-profile service.
Historical names are not silently treated as current.

## Asset Inventory Contract

The inventory covers at least tools/install_debugger.py, tools/preflight.py,
tools/quality_gate.py, tools/security_gate.py, tools/live/** and
tests/integration/test_post_install_browser_live.py. It also inspects
tests/live/**, current integration tests, support fixtures and any existing
e2e directory. Every asset receives one of the six issue classifications, a
reason, owner, duplication risk, target scenarios and write scope.

## Scenario Contract

Every RC1 scenario record contains stable ID, host/environment, precondition,
exact commands and consent mode, expected transition, assertions, required
services, timeout, bounded retries, cleanup/rollback, evidence references,
checksum status, defect severity and final verification-state classification.

Required IDs:

| ID | Scenario |
|---|---|
| RC1-S01 | Local baseline |
| RC1-S02 | WSL2 pre-live diagnostics |
| RC1-S03 | WSL2 fresh install |
| RC1-S04 | Post-install browser/API/service acceptance |
| RC1-S05 | WSL2 re-run/reconcile |
| RC1-S06 | WSL2 update |
| RC1-S07 | Missing prerequisite fail-closed |
| RC1-S08 | Partial-state recovery |
| RC1-S09 | Restart resilience |
| RC1-S10 | Native Linux fresh install |
| RC1-S11 | Native Linux reconcile |
| RC1-S12 | Native Linux update |
| RC1-CI01 | PR/Push Python quality gate |
| RC1-CI02 | Conda Python compatibility matrix |
| RC1-CI03 | Sonar workflow reconciliation and external status |
| RC1-CI04 | Scheduled/manual Classic live workflow and runner qualification |
| RC1-CI05 | Real CI workflow-run and failure-semantic evidence |

## Ordered Slices

### Slice 01 — Requirement matrix, inventory and Three-Amigos gate

Purpose: extract every issue requirement, derive the current Classic service
contract, classify tools/tests, choose canonical test ownership and approve
live scenario/evidence decisions before live execution.

Prerequisites: verified authoring branch and clean baseline.

Allowed write scope: .tiny-swarm/evidence/issue-252/,
.tiny-swarm-world/evidence/classic-public-beta-rc1/ and the workflow-local
requirement baseline. No product source, live state or host configuration.

~~~yaml
slice_id: S252-01
profile: FULL_PATH
owner: Senior Requirement Engineer
secondary_reviewers: [Senior System Architect, Senior Python Automation Developer, Senior Tester, Live Evidence Validation Expert, Senior DevOps]
affected_files: [.tiny-swarm/evidence/issue-252/requirement_matrix.md, .tiny-swarm-world/evidence/classic-public-beta-rc1/three-amigos.md, .tiny-swarm-world/evidence/classic-public-beta-rc1/service-inventory.yaml, documentation/workflow/requirement-matrix.md]
affected_modules: [issue requirements, Classic service inventory, live scenario contract, evidence governance]
affected_contracts: [requirement matrix, RC1 service classification, RC1-S01..RC1-S12, redaction contract, live consent contract]
dependencies: []
parallel_group: SERIAL-252-GATE
file_locks: [.tiny-swarm/evidence/issue-252/, .tiny-swarm-world/evidence/classic-public-beta-rc1/, documentation/workflow/requirement-matrix.md]
contract_locks: [issue-252-matrix, classic-service-inventory, three-amigos-live-decision]
architecture_locks: [linux-wsl2-only, incus-lxc-provider, docker-swarm-first, explicit-live-consent, fail-closed-evidence]
quality_gates:
  targeted: [git diff --check]
  required: [git diff --check, python3 tools/quality_gate.py quality]
documentation:
  arc42: reviewed; update only for verified architecture consequence
  adr: reviewed; no new decision by assumption
stop_conditions: [missing requirement row, unresolved service ownership, unknown canonical test owner, missing redaction contract, missing consent model, guessed command or update semantics]
~~~

Done: every issue sentence, bullet, path, command, service, scenario and
acceptance criterion has a stable matrix ID; every service is classified
exactly once; every named asset has one owner/classification; and the
Three-Amigos record is complete. No live command runs in this slice.

### Slice 02 — Canonical test layout and tool/test separation

Purpose: implement the inventory decision. Keep tools as utilities,
diagnostics, recovery helpers or thin optional runners; keep assertions under
the selected tests/ location.

Prerequisites: S252-01 PASS and canonical location recorded.

Allowed write scope: named tool files, tools/live/, tests/live/,
tests/integration/, tests/e2e/classic/, tests/support/ and directly required
test documentation. Do not create a second framework.

~~~yaml
slice_id: S252-02
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Tester, Senior System Architect, Senior Documentation Engineer]
affected_files: [tools/install_debugger.py, tools/preflight.py, tools/quality_gate.py, tools/security_gate.py, tools/live/, tests/live/test_post_install_browser_live.py, tests/integration/test_post_install_browser_live.py, tests/e2e/classic/, tests/support/]
affected_modules: [diagnostics, static preflight, quality/security utilities, live runner, Classic acceptance tests]
affected_contracts: [tool/test boundary, canonical browser suite, no-duplication contract]
dependencies: [S252-01]
parallel_group: SERIAL-252-TEST-BASE
file_locks: [tools/, tests/live/, tests/integration/, tests/e2e/classic/, tests/support/]
contract_locks: [canonical-classic-test-layout, existing-live-suite-reuse]
architecture_locks: [tools-not-test-assertions, tests-no-live-mutation-by-default]
quality_gates:
  targeted: [git diff --check, python3 tools/quality_gate.py lint, python3 tools/quality_gate.py test]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no update unless source behavior changes
  adr: none
stop_conditions: [duplicate live framework, assertion-heavy logic left in tools without reason, unreviewed relocation, live mutation in default tests]
~~~

Done: inventory classifications are reflected, one canonical post-install
browser/API suite exists, any migration preserves coverage and removes the
duplicate path, thin runners only resolve options/environment, and default
tests remain non-mutating.

### Slice 03 — Deterministic lifecycle, fail-closed and recovery coverage

Purpose: add or extend mocked/static tests for prerequisite failure, partial
state, ownership, idempotent reconcile, safe update, restart classification,
redaction and evidence completeness.

Prerequisites: S252-02 PASS. No live commands.

~~~yaml
slice_id: S252-03
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior Python Automation Developer, Senior System Architect, Live Evidence Validation Expert]
affected_files: [tests/e2e/classic/, tests/live/, tests/integration/, tests/support/, documentation/evidence/]
affected_modules: [acceptance assertions, failure/recovery fixtures, evidence validation]
affected_contracts: [fail-closed state, reconcile idempotence, update preservation, evidence redaction]
dependencies: [S252-02]
parallel_group: SERIAL-252-TEST-COVERAGE
file_locks: [tests/e2e/classic/, tests/live/, tests/integration/, tests/support/, documentation/evidence/]
contract_locks: [scenario-record-schema, evidence-redaction-schema, lifecycle-state-classification]
architecture_locks: [default-tests-no-live-mutation, observed-vs-static-evidence]
quality_gates:
  targeted: [python3 tools/quality_gate.py test, python3 tools/quality_gate.py arch-tests, git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: update only for verified runtime contract change
  adr: none unless a safety decision is required
stop_conditions: [test requires live infrastructure by default, missing negative assertion, evidence accepts raw secret, idempotence inferred without state comparison]
~~~

Done: representative missing prerequisites fail early; partial/ambiguous state
fails closed; reconcile proves no duplicate/destructive drift; update proves
preservation; restart/evidence/redaction and exact RC1 states are testable.

### Slice 13 — Python quality gate and Sonar workflow reconciliation

Purpose: implement the mandatory PR/Push Python quality workflow and reconcile
the existing Sonar workflow into a non-duplicating external analysis gate.

The canonical command remains `python3 tools/quality_gate.py quality` in a
locked Linux CI environment. `sonar_check.yml` must either consume the same
verified quality/coverage contract or clearly own only the external SonarCloud
publication step. A missing token, skipped scan, unavailable status or failed
quality stage is recorded as non-success and cannot satisfy RC1.

~~~yaml
slice_id: S252-13
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior Python Automation Developer, Senior System Architect, Senior Documentation Engineer, Release Baseline Governance Expert]
affected_files: [.github/workflows/python-quality-gate.yml, .github/workflows/sonar_check.yml, documentation/governance/ci-quality-gates.md, tests/test_ci_workflow_contract.py]
affected_modules: [GitHub Actions quality gate, coverage handoff, SonarCloud external analysis]
affected_contracts: [QUALITY.md gate contract, PR/push status contract, external-gate state contract]
dependencies: [S252-03]
parallel_group: SERIAL-252-CI
file_locks: [.github/workflows/, documentation/governance/ci-quality-gates.md, tests/test_ci_workflow_contract.py]
contract_locks: [python-quality-gate, sonar-external-status, ci-failure-semantics]
architecture_locks: [no-live-mutation-in-default-ci, locked-dependencies, observed-vs-inferred-status]
quality_gates:
  targeted: [git diff --check, python3 tools/quality_gate.py test]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no update; CI governance only unless verified runtime behavior changes
  adr: none unless an external-gate safety boundary changes
stop_conditions: [duplicate-quality-authority, unpinned-install, missing-failure-status, sonar-skip-not-green, live-mutation-in-default-job]
~~~

Done: PR and push triggers run the canonical quality gate; Sonar responsibility
is explicit; coverage and external status are observable; no hosted default
job mutates Incus, Docker, Swarm, networking or service state.

### Slice 14 — Conda Python compatibility matrix

Purpose: provide `python-compatibility.yml` as a real Conda-based matrix for
the supported Python versions and prove locked dependency installation and
the full deterministic test contract on each matrix entry.

The initial matrix is Python 3.12 and 3.13 because the project declares
`requires-python >=3.12`, the lock was generated with Python 3.12, and the
current local environment is Python 3.13. The implementation must verify this
against actual package resolution; unsupported entries fail the slice rather
than being silently removed.

~~~yaml
slice_id: S252-14
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Tester, Senior System Architect, Senior Requirement Engineer]
affected_files: [.github/workflows/python-compatibility.yml, environment.yml, tests/test_ci_workflow_contract.py, documentation/governance/ci-quality-gates.md]
affected_modules: [Conda environment, Python compatibility matrix, locked dependency installation]
affected_contracts: [supported-python-matrix, requirements-lock, deterministic-test-suite]
dependencies: [S252-13]
parallel_group: SERIAL-252-CI
file_locks: [.github/workflows/python-compatibility.yml, environment.yml, tests/test_ci_workflow_contract.py]
contract_locks: [conda-matrix, locked-install, version-support]
architecture_locks: [python-312-baseline, no-runtime-architecture-change, no-unpinned-ci-dependencies]
quality_gates:
  targeted: [git diff --check, python3 tools/quality_gate.py test]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no update; compatibility verification only
  adr: none
stop_conditions: [matrix-version-guess, conda-resolution-failure, lock-bypass, matrix-entry-not-executed, platform-dependent-test-forbidden]
~~~

Done: every declared matrix entry installs the locked environment, runs the
required deterministic suite and publishes an explicit result; a failed or
unavailable entry blocks the compatibility gate.

### Slice 15 — Scheduled/manual Classic live workflow and runner qualification

Purpose: provide `nightly-classic-live.yml` for the automatable Classic live
chain while proving that the selected runner is actually capable of the
required Linux/WSL2 or native-Linux target.

GitHub-hosted runners are not treated as Classic-capable by assumption. The
workflow requires a documented self-hosted runner label set, protected
environment approval, target ownership, credentials/reference inputs, redacted
artifact storage and an explicit stop/fail-closed contract. The schedule and
`workflow_dispatch` paths must make disabled or unavailable live execution
visible as `BLOCKED`/`UNVERIFIED`, never as a green run.

~~~yaml
slice_id: S252-15
profile: FULL_PATH
owner: Senior DevOps
secondary_reviewers: [Senior Tester, Senior System Architect, Live Evidence Validation Expert, Senior Requirement Engineer]
affected_files: [.github/workflows/nightly-classic-live.yml, tools/live/, tests/e2e/classic/, documentation/evidence/live-greenpath-evidence-contract.md, documentation/governance/ci-quality-gates.md]
affected_modules: [GitHub Actions live orchestration, self-hosted runner, Classic E2E, redacted evidence]
affected_contracts: [live-consent, runner-capability, live-evidence, failure-state-classification]
dependencies: [S252-13, S252-14]
parallel_group: SERIAL-252-CI-LIVE
file_locks: [.github/workflows/nightly-classic-live.yml, tools/live/, tests/e2e/classic/, documentation/evidence/]
contract_locks: [classic-live-runner, explicit-live-approval, redacted-evidence, no-live-success-on-skip]
architecture_locks: [linux-wsl2-only, no-hosted-runner-substitution, serialized-live-mutation, no-raw-secrets]
quality_gates:
  targeted: [git diff --check, python3 tools/quality_gate.py test]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: review deployment/runtime view only if runner changes supported topology
  adr: required before changing the accepted live-consent or runner boundary
stop_conditions: [runner-label-missing, target-ownership-missing, environment-approval-missing, credential-reference-missing, live-consent-missing, unredacted-artifact, hosted-runner-fallback, partial-run-not-green]
~~~

Done: a real scheduled/manual workflow selects only an approved capable
self-hosted runner, executes the canonical live chain, stores redacted evidence
and reports `LIVE_VERIFIED`, `LIVE_BLOCKED_BEFORE_MUTATION`,
`LIVE_FAILED_AFTER_MUTATION`, `LIVE_PREREQUISITE_MISSING` or `LIVE_PARTIAL`
without collapsing non-success states.

### Slice 16 — Real CI workflow runs and failure-semantic evidence

Purpose: execute the new PR/push, Conda, Sonar and Classic-live workflows and
capture their actual run IDs, commit, trigger, runner, duration, statuses,
artifacts, external-gate state and failure classification.

Prerequisites: S252-13 through S252-15 implemented; CI permissions and protected
environment are verified; no required job remains only YAML-static evidence.

~~~yaml
slice_id: S252-16
profile: FULL_PATH
owner: Release Baseline Governance Expert
secondary_reviewers: [Senior Tester, Senior DevOps, Senior System Architect, Live Evidence Validation Expert, Issue Completion Auditor]
affected_files: [.tiny-swarm-world/evidence/issue-252/, .tiny-swarm-world/evidence/classic-public-beta-rc1/ci/, documentation/workflow/]
affected_modules: [GitHub Actions run evidence, external status, RC1 gate aggregation]
affected_contracts: [ci-run-evidence, required-checks, sonar-status, live-state-classification, final-rc1-gate]
dependencies: [S252-13, S252-14, S252-15]
parallel_group: SERIAL-252-CI-EVIDENCE
file_locks: [.tiny-swarm-world/evidence/issue-252/, .tiny-swarm-world/evidence/classic-public-beta-rc1/ci/]
contract_locks: [run-evidence, failure-semantics, external-gate-verification]
architecture_locks: [observed-vs-inferred, no-green-on-unverified, evidence-redaction]
quality_gates:
  targeted: [git diff --check, python3 tools/quality_gate.py test]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no update from CI status alone
  adr: none
stop_conditions: [missing-run-id, missing-commit, unknown-check, unavailable-sonar-status, skipped-required-job, missing-runner-proof, missing-redaction, non-success-aggregated-as-green]
~~~

Done: real workflow-run evidence exists for every required CI path; all
required checks and Sonar status are observable; missing, skipped, blocked,
failed or unverified paths remain non-success and feed the final RC1 decision.

### Slice 04 — WSL2 diagnostics and fresh install

Purpose: execute RC1-S02 and RC1-S03 on an approved disposable/recoverable
WSL2 target after explicit consent.

Prerequisites: S252-03 PASS; Three-Amigos PASS; explicit consent; WSL2,
systemd, filesystem, Incus and resource prerequisites; target ownership;
redaction and cleanup plan.

Commands are executed from WSL/Linux, never Windows PowerShell:

~~~bash
python3 tools/install_debugger.py --live
# Explicit operator consent is required for this mutating command.
./install.sh --headless --confirm-reset --non-interactive-live-approval
~~~

The second command is mutating and is never run automatically by workflow
authoring or by a default quality gate.

~~~yaml
slice_id: S252-04
profile: FULL_PATH
owner: Senior DevOps
secondary_reviewers: [Senior Python Automation Developer, Senior System Architect, Senior Tester, Live Evidence Validation Expert]
affected_files: [.tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/RC1-S02/, .tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/RC1-S03/]
affected_modules: [WSL2 diagnostics, Incus/LXC, Docker Engine, Swarm, routing, secrets, artifacts, services]
affected_contracts: [WSL2 consent, fresh-install phase order, redacted evidence, cleanup/rollback]
dependencies: [S252-03]
parallel_group: SERIAL-252-LIVE-WSL2
file_locks: [.tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/]
contract_locks: [live-run-template, live-greenpath-evidence-contract, wsl2-fresh-install]
architecture_locks: [explicit-live-consent, lxc-native-only, verify-after-apply, no-raw-secrets]
quality_gates:
  targeted: [python3 tools/install_debugger.py, python3 tools/preflight.py]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no update from evidence alone
  adr: none
stop_conditions: [missing-consent, missing-prerequisite, unsupported-host, unsafe-filesystem, ownership-mismatch, unredacted-output, failed-preflight, mutation-without-verification]
~~~

Done: WSL2 diagnostics and the full phase sequence are recorded; topology,
Docker, Swarm, required services, routing and evidence are observed or the
exact blocker state is recorded. No LIVE_VERIFIED claim exists without a
complete redacted bundle.

### Slice 05 — WSL2 post-install acceptance and reconcile

Purpose: execute RC1-S04 and RC1-S05 on the controlled WSL2 installation.

Prerequisites: S252-04 result, canonical suite, service inventory, explicit
consent for re-run/browser/API checks.

~~~yaml
slice_id: S252-05
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior DevOps, Senior Python Automation Developer, Live Evidence Validation Expert, Senior System Architect]
affected_files: [.tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/RC1-S04/, .tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/RC1-S05/]
affected_modules: [post-install service acceptance, browser/API checks, reconcile]
affected_contracts: [canonical browser suite, service readiness, idempotent rerun, no-drift evidence]
dependencies: [S252-04]
parallel_group: SERIAL-252-LIVE-WSL2
file_locks: [.tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/]
contract_locks: [service-acceptance, reconcile, redaction]
architecture_locks: [service-boundary-ownership, observed-readiness, no-duplicate-state]
quality_gates:
  targeted: [python3 tools/quality_gate.py test]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no update unless verified behavior changes architecture
  adr: none
stop_conditions: [missing-required-service, credential-leak, duplicate-suite-execution, drift, unintended-destruction, partial-evidence]
~~~

Done: every required service is checked; browser/API output is summarized and
redacted; the exact current reconcile command is recorded; the second run
proves no duplicate nodes/stacks, no unintended destruction, preserved
routes/secrets/services and converged verification.

### Slice 06 — WSL2 update and post-update acceptance

Purpose: execute RC1-S06 with one safe, reversible, Three-Amigos-approved
change on healthy WSL2 state.

~~~yaml
slice_id: S252-06
profile: FULL_PATH
owner: Senior DevOps
secondary_reviewers: [Senior Python Automation Developer, Senior Tester, Senior System Architect, Live Evidence Validation Expert]
affected_files: [.tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/RC1-S06/]
affected_modules: [update/reconcile workflow, service readiness, rollback]
affected_contracts: [safe-update, preservation, rollback-evidence]
dependencies: [S252-05]
parallel_group: SERIAL-252-LIVE-WSL2
file_locks: [.tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/]
contract_locks: [update-contract, rollback-contract]
architecture_locks: [non-destructive-reconcile, verify-after-apply]
quality_gates:
  targeted: [python3 tools/quality_gate.py test]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no update unless verified deployment/runtime behavior changes
  adr: no new policy without architecture review
stop_conditions: [unsafe-change, missing-rollback, unrelated-state-loss, failed-readiness, unverified-update, secret-exposure]
~~~

Done: exact update command/change is recorded; selected change converges;
unrelated healthy state remains valid; post-update acceptance and cleanup/
rollback evidence are complete.

### Slice 07 — WSL2 failure, recovery and restart resilience

Purpose: execute RC1-S07, RC1-S08 and RC1-S09 where safe; otherwise record the
exact non-passed state.

~~~yaml
slice_id: S252-07
profile: FULL_PATH
owner: Senior DevOps
secondary_reviewers: [Senior Tester, Senior Python Automation Developer, Senior System Architect, Live Evidence Validation Expert]
affected_files: [.tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/RC1-S07/, .tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/RC1-S08/, .tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/RC1-S09/]
affected_modules: [fail-closed preflight, partial-state recovery, restart resilience, diagnostics]
affected_contracts: [failure-state, recovery, restart, cleanup]
dependencies: [S252-06]
parallel_group: SERIAL-252-LIVE-WSL2-RECOVERY
file_locks: [.tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/]
contract_locks: [fail-closed-contract, recovery-contract, restart-evidence]
architecture_locks: [ownership-scoped-cleanup, no-unsafe-repair, live-state-classification]
quality_gates:
  targeted: [python3 tools/quality_gate.py test]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: update only after verified recovery/runtime behavior
  adr: required if a new safety decision is proposed
stop_conditions: [failure-after-mutation-without-recovery, ambiguous-state-repair, restart-not-safe, cleanup-unclear, evidence-incomplete]
~~~

Done: prerequisite failures stop before unsafe mutation; controlled partial
state reuses valid state or fails closed; restart evidence covers Incus,
nodes, Docker, Swarm, routing and required services; defects receive severity
and regression disposition.

### Slice 08 — Native Linux fresh install and acceptance

Purpose: execute RC1-S10 and native-Linux post-install acceptance on a separate
native-Linux target. WSL2 evidence cannot substitute.

~~~yaml
slice_id: S252-08
profile: FULL_PATH
owner: Senior DevOps
secondary_reviewers: [Senior Python Automation Developer, Senior Tester, Senior System Architect, Live Evidence Validation Expert]
affected_files: [.tiny-swarm-world/evidence/classic-public-beta-rc1/native_linux/RC1-S10/, .tiny-swarm-world/evidence/classic-public-beta-rc1/native_linux/RC1-S04/]
affected_modules: [native Linux host, Incus/LXC, Docker, Swarm, services and acceptance]
affected_contracts: [native-linux-fresh-install, service-acceptance, redacted-evidence]
dependencies: [S252-03]
parallel_group: SERIAL-252-LIVE-NATIVE
file_locks: [.tiny-swarm-world/evidence/classic-public-beta-rc1/native_linux/]
contract_locks: [native-linux-live, service-acceptance]
architecture_locks: [native-linux-supported-target, lxc-native-only, explicit-live-consent]
quality_gates:
  targeted: [python3 tools/install_debugger.py, python3 tools/preflight.py, python3 tools/quality_gate.py test]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no update from runtime evidence alone
  adr: none
stop_conditions: [missing-consent, missing-prerequisite, unsupported-target, failed-preflight, mutation-without-verification, unredacted-evidence]
~~~

Done: native fresh install follows canonical phases and independently
evidences required services, routing, secrets, artifacts, readiness and
acceptance.

### Slice 09 — Native Linux reconcile and acceptance

Purpose: execute RC1-S11 on healthy native-Linux state.

~~~yaml
slice_id: S252-09
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior DevOps, Senior Python Automation Developer, Live Evidence Validation Expert, Senior System Architect]
affected_files: [.tiny-swarm-world/evidence/classic-public-beta-rc1/native_linux/RC1-S11/]
affected_modules: [native Linux reconcile, service/browser/API acceptance]
affected_contracts: [native-reconcile, service-readiness, no-drift-evidence]
dependencies: [S252-08]
parallel_group: SERIAL-252-LIVE-NATIVE
file_locks: [.tiny-swarm-world/evidence/classic-public-beta-rc1/native_linux/]
contract_locks: [reconcile-contract, service-acceptance]
architecture_locks: [idempotent-reconcile, observed-state-only]
quality_gates:
  targeted: [python3 tools/quality_gate.py test]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no update unless verified behavior changes runtime/deployment
  adr: none
stop_conditions: [duplicate-state, unintended-destruction, service-regression, missing-evidence, credential-leak]
~~~

Done: re-run preserves healthy state, routes, secrets and services; no
duplicates or unintended destruction; required acceptance is rerun and
independently evidenced.

### Slice 10 — Native Linux update and acceptance

Purpose: execute RC1-S12 with the same approved safe/reversible update contract.

~~~yaml
slice_id: S252-10
profile: FULL_PATH
owner: Senior DevOps
secondary_reviewers: [Senior Python Automation Developer, Senior Tester, Senior System Architect, Live Evidence Validation Expert]
affected_files: [.tiny-swarm-world/evidence/classic-public-beta-rc1/native_linux/RC1-S12/]
affected_modules: [native Linux update, service readiness, rollback]
affected_contracts: [native-update, preservation, rollback-evidence]
dependencies: [S252-09]
parallel_group: SERIAL-252-LIVE-NATIVE
file_locks: [.tiny-swarm-world/evidence/classic-public-beta-rc1/native_linux/]
contract_locks: [update-contract, rollback-contract]
architecture_locks: [non-destructive-update, verify-after-apply]
quality_gates:
  targeted: [python3 tools/quality_gate.py test]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: no update unless verified deployment/runtime behavior changes
  adr: none unless new safety decision is required
stop_conditions: [unsafe-change, missing-rollback, unrelated-state-loss, failed-readiness, unverified-update, evidence-incomplete]
~~~

Done: selected change converges; unrelated healthy state remains valid;
post-update acceptance is complete and redacted; update failure remains an
explicit blocker/rejection.

## Authorized RC1 Remediation Addendum — 2026-08-23

The user confirmed that implementation remains within Issue #252 Classic RC1
stabilization and must follow the accepted
`adr-traefik-managed-or-operator-ca.adoc`. Existing uncommitted changes are
candidate patches only. Each remediation slice must adopt, repair or reject
them through its declared file scope; no candidate evidence is success evidence
until verified on the exact committed candidate.

### Slice R01 — Canonical TLS contract and CA lifecycle

Purpose: implement one typed TLS resolution contract with external-CA
precedence, managed-CA fallback, a separately signed ingress leaf, canonical
trust-bundle discovery, protected local state and deterministic reuse without
silent rotation.

Prerequisites: S252-03 PASS and the accepted managed-or-operator CA ADR. The
listed `domain/ingress/`, `application/ports/` and `adapters/ingress/` paths are
explicitly authorized create scopes when no suitable existing module exists.

```yaml
slice_id: S252-R01
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Senior Tester, Senior Security Sandbox Engineer]
affected_files: [src/tiny_swarm_world/domain/ingress/, src/tiny_swarm_world/application/ports/, src/tiny_swarm_world/application/services/deployment/, src/tiny_swarm_world/infrastructure/adapters/ingress/, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/swarm/stack_prerequisite_registry.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py, src/tiny_swarm_world/infrastructure/composition_configuration.py, src/tiny_swarm_world/infrastructure/composition_runtime.py, src/tiny_swarm_world/infrastructure/composition_deployment.py, src/tiny_swarm_world/installer.py, tests/domain/ingress/, tests/application/services/deployment/, tests/infrastructure/adapters/ingress/, tests/infrastructure/adapters/clients/lxc/swarm/test_stack_prerequisite_registry.py, tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py, tests/infrastructure/test_composition.py, tests/infrastructure/test_lxc_runtime_logging.py, tests/test_installer.py]
affected_modules: [TLS domain contract, TLS resolution port, managed PKI adapter, installer and runtime composition]
affected_contracts: [canonical-tls-contract, external-ca-precedence, managed-ca-idempotent-reuse, canonical-trust-bundle]
dependencies: [S252-03]
prerequisites: [S252-03 PASS, accepted managed-or-operator CA ADR]
issue_completion_evidence_path: .tiny-swarm/evidence/issue-252/
requirement_to_verification: [REQ-252-051..REQ-252-055 -> focused TLS contract and lifecycle tests]
shared_files: [src/tiny_swarm_world/infrastructure/adapters/clients/lxc/swarm/stack_prerequisite_registry.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py, src/tiny_swarm_world/infrastructure/composition_configuration.py, src/tiny_swarm_world/infrastructure/composition_runtime.py, src/tiny_swarm_world/infrastructure/composition_deployment.py, src/tiny_swarm_world/installer.py]
shared_infrastructure: [managed TLS local state, Traefik Docker secret names]
isolated_worktree_required: true
serialized_live_validation_required: true
merge_order_constraints: [before S252-R02 and S252-R06]
parallelization_status: SERIAL_FILE_AND_CONTRACT_LOCKS
parallel_group: SERIAL-252-REMEDIATION
file_locks: [src/tiny_swarm_world/domain/ingress/, src/tiny_swarm_world/application/ports/, src/tiny_swarm_world/application/services/deployment/, src/tiny_swarm_world/infrastructure/adapters/ingress/, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/swarm/stack_prerequisite_registry.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py, src/tiny_swarm_world/infrastructure/composition_configuration.py, src/tiny_swarm_world/infrastructure/composition_runtime.py, src/tiny_swarm_world/infrastructure/composition_deployment.py, src/tiny_swarm_world/installer.py, tests/domain/ingress/, tests/application/services/deployment/, tests/infrastructure/adapters/ingress/, tests/infrastructure/adapters/clients/lxc/swarm/test_stack_prerequisite_registry.py, tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py, tests/infrastructure/test_composition.py, tests/infrastructure/test_lxc_runtime_logging.py, tests/test_installer.py]
contract_locks: [canonical-tls-contract, external-ca-precedence, managed-ca-idempotent-reuse]
architecture_locks: [hexagonal-boundaries, single-tls-resolution-owner, protected-local-state, no-raw-secrets]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.ingress.test_local_tls_contract_resolver tests.test_installer tests.infrastructure.adapters.clients.lxc.swarm.test_stack_prerequisite_registry tests.infrastructure.adapters.clients.test_lxc_swarm_runtime tests.infrastructure.test_composition tests.infrastructure.test_lxc_runtime_logging, python3 tools/quality_gate.py lint, python3 tools/quality_gate.py typecheck]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: required in S252-R07
  adr: implement accepted adr-traefik-managed-or-operator-ca.adoc; do not rewrite history
stop_conditions: [incomplete-external-config-falls-back, mixed-external-managed-material, silent-key-rotation, self-signed-leaf-used-as-ca, private-key-or-pem-in-evidence, ambiguous-canonical-state-path]
```

Done: complete external configuration wins; incomplete external configuration
fails before mutation; managed CA and leaf material validate for chain, SAN and
expiry, persist with owner-only private-key permissions, and are reused
unchanged on rerun; installer, runtime and E2E resolve one trust bundle.

### Slice R02 — Atomic Traefik secret reconciliation and GUI input recovery

Purpose: reconcile the TLS certificate/key pair and operator-owned dashboard
htpasswd as ordered, redaction-safe pre-apply inputs without irreparable partial
state.

```yaml
slice_id: S252-R02
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Tester, Senior System Architect, Senior Security Sandbox Engineer]
affected_files: [.env.example, src/tiny_swarm_world/domain/configuration/configuration_contract.py, src/tiny_swarm_world/application/services/deployment/ensure_external_swarm_secret.py, src/tiny_swarm_world/application/services/deployment/verify_external_swarm_input.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/swarm/stack_prerequisite_registry.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py, src/tiny_swarm_world/infrastructure/composition_configuration.py, src/tiny_swarm_world/infrastructure/composition_deployment.py, src/tiny_swarm_world/installer.py, tests/domain/configuration/test_configuration_contract.py, tests/application/services/deployment/test_ensure_external_swarm_secret.py, tests/application/services/deployment/test_verify_external_swarm_input.py, tests/infrastructure/adapters/clients/lxc/swarm/test_stack_prerequisite_registry.py, tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py, tests/test_install_script.py, tests/test_installer.py]
affected_modules: [configuration contract, external Swarm input services, LXC Swarm prerequisites, deployment composition, installer reset guard]
affected_contracts: [atomic-secret-pair, traefik-gui-operator-secret, secret-redaction, verify-before-apply]
dependencies: [S252-R01]
prerequisites: [S252-R01 PASS, canonical TLS contract available]
issue_completion_evidence_path: .tiny-swarm/evidence/issue-252/
requirement_to_verification: [REQ-252-056..REQ-252-057 -> partial-state, ordering and redaction tests]
shared_files: [stack_prerequisite_registry.py, lxc_swarm_runtime.py, composition_configuration.py, installer.py]
shared_infrastructure: [Docker Swarm secret store, Traefik deployment]
isolated_worktree_required: true
serialized_live_validation_required: true
merge_order_constraints: [after S252-R01, before S252-R06]
parallelization_status: SERIAL_SHARED_TLS_LOCKS
parallel_group: SERIAL-252-REMEDIATION
file_locks: [.env.example, src/tiny_swarm_world/domain/configuration/configuration_contract.py, src/tiny_swarm_world/application/services/deployment/ensure_external_swarm_secret.py, src/tiny_swarm_world/application/services/deployment/verify_external_swarm_input.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc/swarm/stack_prerequisite_registry.py, src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py, src/tiny_swarm_world/infrastructure/composition_configuration.py, src/tiny_swarm_world/infrastructure/composition_deployment.py, src/tiny_swarm_world/installer.py, tests/domain/configuration/test_configuration_contract.py, tests/application/services/deployment/, tests/infrastructure/adapters/clients/lxc/swarm/test_stack_prerequisite_registry.py, tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py, tests/test_install_script.py, tests/test_installer.py]
contract_locks: [atomic-secret-pair, traefik-gui-operator-secret, secret-redaction]
architecture_locks: [verify-before-apply, protected-local-state, no-raw-secrets]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_ensure_external_swarm_secret tests.application.services.deployment.test_verify_external_swarm_input tests.domain.configuration.test_configuration_contract tests.infrastructure.adapters.clients.lxc.swarm.test_stack_prerequisite_registry tests.infrastructure.adapters.clients.test_lxc_swarm_runtime tests.test_install_script tests.test_installer]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: required in S252-R07
  adr: no new decision unless rollback semantics exceed the accepted TLS ADR
stop_conditions: [partial-secret-state-not-recoverable, stack-apply-before-input-verification, htpasswd-value-in-log-command-or-evidence, missing-value-after-destructive-reset]
```

Done: none/both/cert-only/key-only/second-create failure and retry paths are
deterministic and recoverable or explicitly fail closed; the stack never
applies with an invalid pair; htpasswd material remains operator-owned and
redacted.

### Slice R03 — Incus provider readiness and restart classification

Purpose: make daemon readiness bounded and ordered before provider inspection,
with typed and redacted timeout, unavailable, permission and unknown states.

```yaml
slice_id: S252-R03
profile: FULL_PATH
owner: Senior DevOps
secondary_reviewers: [Senior Python Automation Developer, Senior Tester]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/preflight/lxc_provider_preflight.py, tests/infrastructure/adapters/preflight/test_lxc_provider_preflight.py]
affected_modules: [Incus/LXC provider preflight]
affected_contracts: [bounded-provider-readiness, waitready-before-inspection, typed-provider-failure]
dependencies: [S252-03]
prerequisites: [S252-03 PASS, Incus and LXC commands remain non-mutating in tests]
issue_completion_evidence_path: .tiny-swarm/evidence/issue-252/
requirement_to_verification: [REQ-252-058 -> waitready order and typed timeout tests]
shared_files: []
shared_infrastructure: [Incus daemon state]
isolated_worktree_required: true
serialized_live_validation_required: true
merge_order_constraints: [before S252-R04 and dependent restart rerun]
parallelization_status: SERIAL_SHARED_PROVIDER_STATE
parallel_group: SERIAL-252-REMEDIATION
file_locks: [src/tiny_swarm_world/infrastructure/adapters/preflight/lxc_provider_preflight.py, tests/infrastructure/adapters/preflight/test_lxc_provider_preflight.py]
contract_locks: [bounded-provider-readiness, provider-error-classification]
architecture_locks: [no-live-mutation-by-preflight, redacted-diagnostics]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_lxc_provider_preflight]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: review in S252-R07
  adr: none
stop_conditions: [unbounded-wait, provider-inspection-before-waitready, raw-output-in-evidence, timeout-classification-unknown]
```

### Slice R04 — Managed-LXC artifact readiness and timeout semantics

Purpose: execute Docker/storage probes inside the selected manager container,
preserve host ownership for local build inputs and classify
`subprocess.TimeoutExpired` as a bounded typed result.

```yaml
slice_id: S252-R04
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Tester, Senior DevOps]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/preflight/__init__.py, src/tiny_swarm_world/infrastructure/adapters/preflight/artifact_readiness.py, src/tiny_swarm_world/infrastructure/composition_runtime.py, src/tiny_swarm_world/infrastructure/composition_setup.py, tests/infrastructure/adapters/preflight/test_artifact_readiness.py]
affected_modules: [artifact readiness adapters, provider-aware composition]
affected_contracts: [artifact-probe-location, timeout-classification, read-only-probe]
dependencies: [S252-R03]
prerequisites: [S252-R03 PASS, provider timeout taxonomy fixed]
issue_completion_evidence_path: .tiny-swarm/evidence/issue-252/
requirement_to_verification: [REQ-252-059 -> managed command, timeout and redaction tests]
shared_files: [src/tiny_swarm_world/infrastructure/composition_runtime.py, src/tiny_swarm_world/infrastructure/composition_setup.py]
shared_infrastructure: [managed LXC manager node]
isolated_worktree_required: true
serialized_live_validation_required: true
merge_order_constraints: [after S252-R03, before S252-R06]
parallelization_status: SERIAL_PROVIDER_AND_COMPOSITION_LOCKS
parallel_group: SERIAL-252-REMEDIATION
file_locks: [src/tiny_swarm_world/infrastructure/adapters/preflight/__init__.py, src/tiny_swarm_world/infrastructure/adapters/preflight/artifact_readiness.py, src/tiny_swarm_world/infrastructure/composition_runtime.py, src/tiny_swarm_world/infrastructure/composition_setup.py, tests/infrastructure/adapters/preflight/test_artifact_readiness.py]
contract_locks: [artifact-probe-location, timeout-classification]
architecture_locks: [bounded-provider-readiness, no-readiness-mutation, no-raw-command-output]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.preflight.test_artifact_readiness]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: review in S252-R07
  adr: none
stop_conditions: [host-probe-substituted-for-managed-node, timeout-escapes-untyped, readiness-probe-mutates, stdout-or-stderr-persisted]
```

### Slice R05 — Native-Linux kernel prerequisite verification

Purpose: verify bridge-netfilter and forwarding controls without silently
mutating operator-owned host state.

```yaml
slice_id: S252-R05
profile: FULL_PATH
owner: Senior DevOps
secondary_reviewers: [Senior Python Automation Developer, Senior Tester, Senior Documentation Engineer]
affected_files: [src/tiny_swarm_world/infrastructure/adapters/host/native_linux_host_preparation.py, tests/infrastructure/adapters/host/test_host_preparation.py, documentation/user_guide/installation.adoc]
affected_modules: [native Linux host preparation, operator remediation documentation]
affected_contracts: [native-kernel-prerequisites, fail-closed-host-check, operator-owned-host-mutation]
dependencies: [S252-03]
prerequisites: [S252-03 PASS, read-only native host contract retained]
issue_completion_evidence_path: .tiny-swarm/evidence/issue-252/
requirement_to_verification: [REQ-252-060 -> proc-sys fixture tests and operator documentation]
shared_files: []
shared_infrastructure: [native Linux kernel controls]
isolated_worktree_required: true
serialized_live_validation_required: true
merge_order_constraints: [before Native-Linux live slices and S252-R06]
parallelization_status: SERIAL_HOST_SAFETY_LOCK
parallel_group: SERIAL-252-REMEDIATION
file_locks: [src/tiny_swarm_world/infrastructure/adapters/host/native_linux_host_preparation.py, tests/infrastructure/adapters/host/test_host_preparation.py, documentation/user_guide/installation.adoc]
contract_locks: [native-kernel-prerequisites, operator-owned-host-mutation]
architecture_locks: [read-only-default-preflight, explicit-live-consent]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.host.test_host_preparation]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: review in S252-R07
  adr: none unless automatic host mutation is proposed
stop_conditions: [implicit-sysctl-or-module-mutation, missing-remediation, cleanup-claims-unperformed-rollback, host-value-leak]
```

### Slice R06 — Bounded E2E readiness and composition integration

Purpose: validate the combined wiring and keep the canonical Classic live suite
bounded by one monotonic deadline while consuming the canonical TLS contract.

```yaml
slice_id: S252-R06
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior Python Automation Developer, Senior System Architect, Live Evidence Validation Expert]
affected_files: [tests/e2e/classic/test_post_install_browser_live.py, tests/infrastructure/test_composition.py]
affected_modules: [Classic post-install acceptance, composition integration]
affected_contracts: [canonical-classic-suite, monotonic-readiness-deadline, canonical-trust-bundle, combined-remediation-wiring]
dependencies: [S252-R01, S252-R02, S252-R04, S252-R05]
prerequisites: [S252-R01 PASS, S252-R02 PASS, S252-R04 PASS, S252-R05 PASS]
issue_completion_evidence_path: .tiny-swarm/evidence/issue-252/
requirement_to_verification: [REQ-252-055 and REQ-252-061 -> composition and bounded E2E tests]
shared_files: [tests/e2e/classic/test_post_install_browser_live.py, tests/infrastructure/test_composition.py]
shared_infrastructure: [Classic service endpoints when live rerun is later authorized]
isolated_worktree_required: true
serialized_live_validation_required: true
merge_order_constraints: [after all product remediation slices, before documentation consolidation]
parallelization_status: SERIAL_INTEGRATION_JOIN
parallel_group: SERIAL-252-REMEDIATION
file_locks: [tests/e2e/classic/test_post_install_browser_live.py, tests/infrastructure/test_composition.py]
contract_locks: [canonical-classic-suite, monotonic-readiness-deadline, combined-remediation-wiring]
architecture_locks: [one-live-test-framework, no-live-mutation-by-default, observed-vs-inferred]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.e2e.classic.test_post_install_browser_live tests.infrastructure.test_composition]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: review in S252-R07
  adr: verify canonical TLS contract only
stop_conditions: [per-service-timeouts-exceed-global-deadline, timeout-misclassified-as-success, duplicate-live-framework, composition-test-requires-live-system]
```

### Slice R07 — Documentation, requirement and evidence synchronization

Purpose: reconcile Arc42, operator configuration, the complete requirement
matrix and all six issue evidence files with the accepted implementations and
exact candidate SHA. Candidate `.codex/evidence/**` is reviewed and redacted,
never accepted blindly.

```yaml
slice_id: S252-R07
profile: FULL_PATH
owner: Senior Documentation Engineer
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Tester, Live Evidence Validation Expert]
affected_files: [documentation/arc42/06_runtime_view.adoc, documentation/arc42/07_deployment_view.adoc, documentation/arc42/08_configuration/config-contract-inventory.md, documentation/arc42/08_configuration/operator-configuration-contract.md, documentation/arc42/08_concepts.adoc, documentation/arc42/09_decisions/, documentation/workflow/requirement-matrix.md, .tiny-swarm/evidence/issue-252/, .codex/evidence/]
affected_modules: [architecture documentation, operator contract, issue traceability and evidence]
affected_contracts: [requirement-to-implementation, planned-vs-implemented, evidence-redaction, canonical-tls-documentation]
dependencies: [S252-R01, S252-R02, S252-R03, S252-R04, S252-R05, S252-R06]
prerequisites: [all S252-R01..S252-R06 consolidation evidence accepted]
issue_completion_evidence_path: .tiny-swarm/evidence/issue-252/
requirement_to_verification: [REQ-252-062 -> documentation, SHA and redaction audit]
shared_files: [documentation/arc42/, documentation/workflow/requirement-matrix.md, .tiny-swarm/evidence/issue-252/, .codex/evidence/]
shared_infrastructure: []
isolated_worktree_required: true
serialized_live_validation_required: false
merge_order_constraints: [after S252-R06, before exact-candidate acceptance]
parallelization_status: SERIAL_EVIDENCE_JOIN
parallel_group: SERIAL-252-REMEDIATION
file_locks: [documentation/arc42/, documentation/workflow/requirement-matrix.md, .tiny-swarm/evidence/issue-252/, .codex/evidence/]
contract_locks: [requirement-to-implementation, evidence-redaction, canonical-tls-documentation]
architecture_locks: [arc42-adr-consistency, observed-vs-inferred, no-raw-secrets]
quality_gates:
  targeted: [git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: required synchronization
  adr: preserve both superseded history and accepted replacement
stop_conditions: [stale-requirement-row, old-evidence-attributed-to-new-code, raw-secret-or-private-key, documented-behavior-not-implemented, adr-history-rewritten]
```

### Slice R08 — Local candidate acceptance and dependent rerun handoff

Purpose: freeze the exact candidate, run targeted gates followed by the full
local quality gate, then authorize only explicitly consented WSL2 reruns.
Native Linux and external CI/Sonar/runner paths keep their actual non-success
state until separately executed.

```yaml
slice_id: S252-R08
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior DevOps, Issue Completion Auditor]
affected_files: [.tiny-swarm/evidence/issue-252/test_results.md, .tiny-swarm/evidence/issue-252/acceptance_checklist.md, .tiny-swarm/evidence/issue-252/remaining_risks.md, .tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/]
affected_modules: [local quality evidence, WSL2 dependent rerun evidence, completion handoff]
affected_contracts: [exact-candidate-verification, local-vs-live-state, dependent-rerun, no-rc1-overclaim]
dependencies: [S252-R07]
prerequisites: [S252-R07 PASS, exact candidate SHA frozen, clean candidate worktree]
issue_completion_evidence_path: .tiny-swarm/evidence/issue-252/
requirement_to_verification: [REQ-252-063 -> targeted and full quality evidence]
shared_files: [.tiny-swarm/evidence/issue-252/, .tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/]
shared_infrastructure: [controlled WSL2 Classic target for explicitly consented reruns]
isolated_worktree_required: true
serialized_live_validation_required: true
merge_order_constraints: [after S252-R07, before S252-11 final defect consolidation]
parallelization_status: SERIAL_ACCEPTANCE_GATE
parallel_group: SERIAL-252-REMEDIATION
file_locks: [.tiny-swarm/evidence/issue-252/, .tiny-swarm-world/evidence/classic-public-beta-rc1/wsl2/]
contract_locks: [exact-candidate-verification, local-vs-live-state, dependent-rerun]
architecture_locks: [explicit-live-consent, observed-vs-inferred, no-rc1-overclaim]
quality_gates:
  targeted: [git diff --check, python3 tools/quality_gate.py lint, python3 tools/quality_gate.py arch-lint, python3 tools/quality_gate.py arch-tests, python3 tools/quality_gate.py typecheck, python3 tools/quality_gate.py test]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: verify synchronized state
  adr: verify accepted TLS decision implementation
stop_conditions: [dirty-candidate-after-verification, failed-required-gate, live-command-without-consent, stale-sha, unavailable-native-or-external-check-reported-green]
```

Done: local quality is green on the exact candidate or remains an explicit
failure; WSL2 reruns use explicit consent; Native Linux S252-08..10 and CI
S252-15..16 remain mandatory independent paths before S252-11/S252-12 may
produce final acceptance.

### Slice 11 — Defect classification, fixes and dependent reruns

Purpose: consolidate defects, classify them RC1_BLOCKER, RC1_MAJOR,
RC1_MINOR or RC1_OBSERVATION, add regression coverage for actionable defects
and rerun failed/dependent scenarios.

Prerequisites: S04-S10 evidence and test results. No unrelated refactor.

~~~yaml
slice_id: S252-11
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior Tester, Senior System Architect, Senior Requirement Engineer, Senior DevOps, Live Evidence Validation Expert]
affected_files: [.tiny-swarm-world/evidence/classic-public-beta-rc1/defects/, tests/e2e/classic/, tests/live/, tests/integration/, tests/support/]
affected_modules: [defect fixes, regression tests, scenario reruns, evidence consolidation]
affected_contracts: [RC1 defect policy, regression evidence, rerun dependency map]
dependencies: [S252-R08, S252-07, S252-10, S252-16]
parallel_group: SERIAL-252-REMEDIATION
file_locks: [.tiny-swarm-world/evidence/classic-public-beta-rc1/defects/, tests/e2e/classic/, tests/live/, tests/integration/, tests/support/]
contract_locks: [defect-severity, regression-evidence, rerun-contract]
architecture_locks: [smallest-root-cause-fix, no-guard-weakening, hexagonal-boundaries]
quality_gates:
  targeted: [python3 tools/quality_gate.py test, python3 tools/quality_gate.py typecheck, git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: update only for verified architecture/runtime consequences
  adr: required before changing accepted safety boundary
stop_conditions: [unowned-defect, blocker-waiver, unrelated-refactor, guard-weakening, missing-regression-test, failed-dependent-rerun, unresolved-live-failure]
~~~

Done: every discovery links to evidence; every blocker/major fix has regression
coverage or remains an explicit blocker; dependent scenarios rerun; no failure
is hidden. A fix needing new architecture or outside ownership stops BLOCKED.

### Slice 12 — Evidence audit and final RC1 decision

Purpose: independently audit matrix, service/asset inventories, local quality,
host/scenario bundles, defects/reruns, redaction/checksums and final decision.

~~~yaml
slice_id: S252-12
profile: FULL_PATH
owner: Issue Completion Auditor
secondary_reviewers: [Senior Requirement Engineer, Senior System Architect, Senior Tester, Live Evidence Validation Expert, Release Baseline Governance Expert]
affected_files: [.tiny-swarm/evidence/issue-252/, .tiny-swarm-world/evidence/classic-public-beta-rc1/, documentation/arc42/]
affected_modules: [issue completion, release qualification, evidence audit, architecture synchronization]
affected_contracts: [issue-completion-discipline, live-state-policy, RC1-final-decision]
dependencies: [S252-11, S252-16]
parallel_group: SERIAL-252-FINAL
file_locks: [.tiny-swarm/evidence/issue-252/, .tiny-swarm-world/evidence/classic-public-beta-rc1/, documentation/arc42/]
contract_locks: [requirement-to-evidence, final-rc1-decision]
architecture_locks: [planned-vs-implemented, observed-vs-inferred, arc42-consistency]
quality_gates:
  targeted: [git diff --check, python3 tools/quality_gate.py quality]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: required review; update only from verified behavior or explicit ADR
  adr: review affected decisions; do not rewrite history
stop_conditions:
  - open-requirement
  - missing-evidence
  - unverifiable-live-success
  - raw-secret
  - missing-review
  - inconsistent-arc42
  - external-gate-overclaim
~~~

Done: all issue evidence files exist; every requirement maps to implementation
and verification evidence; every required scenario has host-specific redacted
evidence; exact final decision and the required independent requirement,
architecture, implementation, test/evidence and dependency/deadlock reviews
are recorded.

## Dependency Graph

~~~text
S252-01 -> S252-02 -> S252-03
                       | \
                       |  -> S252-R01 -> S252-R02 --\
                       |  -> S252-R03 -> S252-R04 ---+-> S252-R06 -> S252-R07 -> S252-R08
                       |  -> S252-R05 ---------------/
                       |
                       |  -> S252-04 -> S252-05 -> S252-06 -> S252-07
                       |
                       -> S252-08 -> S252-09 -> S252-10
                       |
                       -> S252-13 -> S252-14 -> S252-15 -> S252-16

S252-R08, S252-07, S252-10 and S252-16 -> S252-11 -> S252-12
~~~

The remediation tracks start after S252-03 and converge before any dependent
live rerun. The host and CI tracks are logically independent only after S252-03, but live
validation remains serialized because targets, credentials, ports, state,
evidence semantics and operator decisions are not assumed isolated. CI
workflow publication and live-run evidence still converge before defect
classification and the final audit.

## Parallel Execution

- Can this workflow run in parallel? CI design and static contract work may
  proceed beside the host tracks after S252-03 only with disjoint worktrees;
  live validation and final evidence remain serialized.
- Conflicting workflows: any workflow changing Classic commands, provider
  lifecycle, Docker/Swarm setup, routing, secrets, artifacts, service stacks,
  live evidence or release governance.
- Shared files: selected Python/configuration surfaces, `.github/workflows/`,
  `environment.yml`, tools/, tests/, documentation/evidence/,
  documentation/arc42/, requirement/evidence paths and runtime targets.
- Shared infrastructure: Incus, managed nodes, Docker Engine/Swarm, ports,
  routes, services, credentials, browser endpoints and evidence roots.
- Requires isolated worktree: yes, for authoring and every implementation
  stream.
- Requires serialized live validation: yes, one approved target/run at a time.
- Merge order: S252-01 -> S252-02 -> S252-03; CI slices S252-13..16 and host
  tracks S252-04..10 may be prepared only in disjoint worktrees; S252-11
  follows all required host/CI evidence; S252-12 is last.
- No parallel live run shares ports, state, credentials or evidence paths.
- Overlapping locks, unclear ownership, contradictory requirements, unsafe
  recovery or unstable contracts force serial execution or a stop.

## Automatic Work Distribution Policy

workflow execute automatically analyzes every slice for safe specialist stream
decomposition across backend, frontend, tests, runtime, documentation, quality,
architecture and security.

It uses real Codex subagents where supported. If unavailable or not visible,
it performs explicit role-based fallback review in the main thread and records
.codex/evidence/slice-<number>-distribution.md before implementation. After
each implemented slice it records .codex/evidence/slice-<number>-consolidation.md.
Codex remains final integration owner for consolidation, tests, evidence,
publication readiness and the RC1 handoff.

Stream map: backend/Python -> Senior Python Automation Developer; frontend ->
N/A; tests -> Senior Tester; runtime/live -> Senior DevOps and Live Evidence
Validation; documentation/arc42 -> Senior Documentation Engineer and
Requirement Lead; quality -> Senior Tester/quality-gate owner; architecture ->
Senior System Architect; security/redaction -> Live Evidence Validation and
security governance; release/completion -> Release Baseline Governance and
Issue Completion Auditor.

Do not parallelize overlapping files, unclear architecture, contradictory
requirements, mandatory ordering, shared migrations, generated-file conflicts,
unclear secrets, weakened safety guards, a Three-Amigos not-safe decision,
shared live infrastructure or live validation without isolated resources.

## Git Worktree Execution Rule

Every implementation uses a dedicated issue worktree and the planned branch
feature/classic-public-beta-rc1-stabilization, after verifying that the branch
is not shared or conflicting. If it exists, verify ownership/base; otherwise
create it from approved current-main baseline.

Workers verify active branch/worktree and locks before writing. No worker
implements on main, master, develop or another shared branch. Workers do not
merge directly; Codex consolidates accepted results after evidence and gates.

Live validation is serialized. Execution stops before live mutation when
consent, target ownership, prerequisites, evidence path, redaction and rollback
are not verified.

## Issue Completion Discipline

- Requirement matrix path: .tiny-swarm/evidence/issue-252/requirement_matrix.md
- Required evidence path: .tiny-swarm/evidence/issue-252/
- Required evidence files: requirement_matrix.md, implementation_summary.md,
  changed_files.md, test_results.md, remaining_risks.md and
  acceptance_checklist.md
- Required CI evidence: real run summaries for `python-quality-gate.yml`,
  `python-compatibility.yml`, reconciled `sonar_check.yml` and
  `nightly-classic-live.yml`, including run ID, commit, trigger, runner,
  status, artifacts, redaction and failure classification.
- Live evidence path:
  .tiny-swarm-world/evidence/classic-public-beta-rc1/<host>/<scenario>/
- Requirement Lead review: S252-01 and S252-12
- System Architect Reviewer: S252-01, every fix slice and S252-12
- Test/Evidence Reviewer: S252-02, S252-03, every scenario and S252-12
- Issue Completion Auditor: S252-12, independent of implementer
- DONE blocking rule: any open/unverified requirement, missing evidence,
  missing redaction/checksum, failed/unverified scenario, ambiguous service
  inventory or unresolved architecture/security blocker forces INCOMPLETE,
  BLOCKED or FAILED, never DONE.

## Quality-Gate Expectations

Authoritative commands from QUALITY.md:

~~~bash
git diff --check
python3 tools/quality_gate.py lint
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py typecheck
python3 tools/quality_gate.py test
python3 tools/quality_gate.py quality
~~~

Run Python commands from Linux/WSL with POSIX paths. Local green is local
evidence only, never live/browser/SonarQube evidence. Live and external states
follow documentation/process/verification-state-policy.md.

CI-specific required gates are part of #252 and are not satisfied by YAML
presence alone:

- `.github/workflows/python-quality-gate.yml` must execute the same locked
  `python3 tools/quality_gate.py quality` contract on PR and push events.
- `.github/workflows/python-compatibility.yml` must execute the declared Conda
  matrix and fail when any matrix entry is missing, skipped or unresolved.
- `.github/workflows/sonar_check.yml` must report external SonarCloud state
  separately and honestly; a missing token or unavailable status is not green.
- `.github/workflows/nightly-classic-live.yml` must use a verified
  self-hosted Classic-capable runner and protected live environment. It must
  never fall back silently to a hosted runner or treat a blocked live job as a
  pass.
- S252-16 must capture real GitHub Actions run evidence, not only local or
  static workflow inspection.

## Documentation Synchronization

Arc42 introduction/goals, constraints, solution strategy, building blocks,
runtime, deployment, quality and risk sections plus the explicit-live-consent
and LXC-native-provider ADRs were reviewed. No Arc42/ADR change is claimed by
this authoring turn because the workflow validates existing behavior and does
not decide a new architecture. Verified drift during execution requires a
reviewed documentation/ADR slice before RC1.

## Stop Conditions

Stop rather than guess when repository/branch/baseline cannot be verified;
matrix is incomplete; service list or test ownership is ambiguous; target,
permissions, prerequisites, credentials, resource contract, consent, evidence,
redaction or rollback is missing; host behavior is inferred across classes;
mutation occurs without explicit consent; reset/destroy scope is unclear;
command/update semantics are unverified; raw output is persisted; tests
duplicate coverage; post-mutation recovery is incomplete; architecture or
ownership is unclear; quality gates fail without classification; required
external status is unavailable for a claim; or an open requirement is hidden.

## Definition of Done

The independent auditor confirms:

1. Matrix and all issue bullets/paths/commands are traced.
2. Tool/test inventory and canonical test ownership are recorded.
3. Deterministic lifecycle, fail-closed, recovery and redaction tests pass.
4. WSL2 and native Linux Fresh/Reconcile/Update execute when required with
   host-specific redacted evidence.
5. Every RC1_REQUIRED service passes required service/browser/API acceptance.
6. Failure/recovery/restart scenarios pass or are explicitly non-passed; none
   is silently skipped.
7. Every blocker/major defect has regression coverage and dependent reruns.
8. Full local quality is green and external status is reported honestly.
9. PR/Push quality, Conda compatibility, Sonar reconciliation and the
   scheduled/manual Classic-live workflow have real successful or explicitly
   non-success evidence; no required CI status is unknown.
10. Final decision is exactly RC1_ACCEPTED, RC1_REJECTED_BLOCKERS or
   RC1_REJECTED_EVIDENCE_INCOMPLETE.
11. Evidence is complete, redacted, checksummed and independently reviewed.
12. Arc42/ADR references match verified behavior.

RC1 acceptance is impossible with an open, blocked, partial, degraded, skipped,
failed-to-apply or failed-to-verify required scenario.

## Commit and Push Plan

Workflow authoring is published as a guarded documentation commit on
feature/workflow-issue-252-remediation-20260823, pushing only HEAD to the
matching origin branch. It must not create/merge a PR, delete a branch,
force-push or run live infrastructure.

Later implementation uses one issue-scoped commit per executable slice after
targeted checks, the full local quality gate and git diff --check. The
implementation branch is not published or merged by this authoring turn.

## Handoff to workflow execute

1. Verify execution baseline `f02d14d3`, the remediation authoring branch,
   `feature/classic-public-beta-rc1-stabilization` implementation worktree,
   locks and S3/S3D preflight.
2. Promote the remediation workflow commit onto the declared implementation
   branch without absorbing unrelated worktree changes.
3. Verify completed historical slices, then execute S252-R01 through S252-R08
   in dependency order with one slice per commit.
4. Execute or verify S252-13 through S252-16 as the mandatory CI layer; do not claim CI
   completion from workflow files without real run evidence.
5. Do not execute S252-04 through S252-10 without Three-Amigos approval,
   explicit live consent and evidence readiness per target.
6. Keep live validation serialized and keep hosted CI free of live mutation.
7. Run issue-completion-auditor in S252-12; it alone decides PASS/DONE or
   INCOMPLETE/BLOCKED/FAILED.
8. A later push auto request keeps workflow-only publication guarded; PR merge
   and branch cleanup require explicit confirmation after the guard is reported.

## Arc42 Check Status

CHECKED_UPDATED_ADR_BASELINE.

Arc42 introduction, constraints, strategy, building blocks, runtime,
deployment, quality and risk sections and the accepted explicit-live-consent
and LXC-native-provider ADRs were reviewed. The accepted
`adr-traefik-managed-or-operator-ca.adoc` and its superseded predecessor are
included in the context pack. Issue #252 preserves Linux/WSL2, Incus/LXC,
Docker Swarm and fail-closed architecture and authorizes only the bounded
remediation scopes above.

## Final Authoring State

This workflow is authored and ready for controlled workflow execute. It is not
implementation evidence, live evidence, a release decision or a grant of
administrator PowerShell access.

## Authoring Publication Handoff

- Branch: `feature/workflow-issue-252-remediation-20260823`
- Commit: recorded after the guarded authoring commit is created.
- Push target: `origin/feature/workflow-issue-252-remediation-20260823`
- Publication verification: `git diff --check` and Context-Pack JSON/hash
  validation must pass before the guarded branch push; push result is recorded
  after publication.
- Pull request/merge: not created by workflow authoring.
- Live/CI execution: not performed by workflow authoring.
- Formal workflow status remains `REMEDIATION_AUTHORED_NOT_EXECUTED` until controlled
  `workflow execute` runs the CI and live slices.
