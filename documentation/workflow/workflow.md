# Workflow: Issue #150 — Secure Traefik GUI

Workflow id: `issue-150-secure-traefik-gui-20260812`

Issue: [#150](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/150)

Authoring branch: `docs/workflow-public-beta-roadmap-20260812`

Planned execution branch: `feature/issue-150-secure-traefik-gui-20260812`

Execution branch: `feature/issue-150-secure-traefik-gui-20260812`

Status: `IN_PROGRESS`

## Executive Summary

Enable a secure, documented and verifiable Traefik dashboard path only after
#123 ISMS, #128 branch/CI governance and #126 ASVS/admin-surface decisions are
complete. The feature must preserve the Docker Swarm/Traefik architecture,
existing Service Access routes and TLS direction. `--api.insecure=true`, raw
credentials and unsecured host exposure remain forbidden.

## Requirement Clarification Gate

- Original request: build #150 after the security and governance foundations.
- Interpreted intent: make Traefik's already-enabled dashboard reachable only
  through an explicitly secured, owned and tested admin route.
- Change type: security-sensitive infrastructure/configuration feature with
  architecture and documentation updates.
- Affected process strand: admin-surface decision -> desired state/config ->
  local tests -> explicit live/browser verification.
- Affected architecture area: `infra/config/compose/traefik/`, domain ingress
  models, compose rendering/adapters, TLS/secret references, arc42 ADR/runtime
  and routing tests.
- Explicit requirements: secure explicit route; existing TLS compatibility;
  Linux/WSL-first operation; no insecure API, raw secrets or unsecured host
  ports; no silent general frontend; preserve Service Access; no live success
  claim before verification.
- Implicit requirements: authentication and authorization must have a clear
  owner; route must be manager/operator/diagnostic scoped; missing TLS/auth
  evidence fails closed; rollback must remove the GUI route without weakening
  existing services.
- Assumptions: current canonical ADR is
  `documentation/arc42/09_decisions/adr-traefik-https-ingress-existing-ca.adoc`
  (the older path in the issue is stale); the existing desired-ingress model
  and route tests remain the architecture entry points.
- Non-goals: `--api.insecure=true`, raw secrets, open ports, general React
  frontend, unrelated service-access redesign and live deployment by default.
- Risks: dashboard route accidentally public, auth middleware not owned, TLS
  secret name/value confusion, route collision or regression of Service Access.
- Open questions: the exact route hostname/path, auth mechanism and exposure
  boundary must be decided in S150-01 from #123/#126 and the ADR; they must not
  be guessed in S150-02.
- Blocking questions: none for authoring; implementation is blocked if S150-01
  cannot produce an approved decision.
- Confidence: 88%.
- Decision: `PROCEED_WITH_ACCEPTED_ASSUMPTIONS` because implementation details
  are intentionally delegated to the architecture gate.

## Target Picture

```text
Traefik dashboard enabled internally
          |
          v
approved TLS + auth/authorization + operator boundary
          |
          v
explicit HTTPS route, tested as desired state
          |
          v
live/browser verification only with explicit consent and evidence
```

## Verified Baseline and Scope

Verified inputs include `infra/config/compose/traefik/docker-compose.yml`, the
canonical Traefik HTTPS ADR, `src/tiny_swarm_world/domain/ingress/desired_state.py`,
`src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py`,
the ingress/domain tests, compose repository tests and routing integration
contracts. The dashboard flag exists; an approved secure GUI route is not
treated as implemented. Scope includes those config/model/adapter/test/docs
surfaces only after S150-01 confirms the exact files. No live commands.

## Architecture, Python, Frontend and Resilience Assessment

- Architecture: keep Traefik as Deployment responsibility and preserve
  hexagonal domain/application boundaries; use desired-state models and
  infrastructure adapters rather than shell details in application code.
- Python automation: likely affected if route/auth data is rendered or
  validated; use existing ports/adapters, typed models, deterministic tests and
  no constructor-time live calls.
- Frontend: no React/browser frontend is authorized. The Traefik built-in
  admin surface may receive a browser/live verification contract only.
- Resilience: missing/invalid TLS or auth references, forbidden insecure mode,
  route collision or incomplete readiness evidence fail closed; rollback means
  the GUI route is absent while existing ingress/service-access paths remain
  valid.

## Ordered Slices

### Slice 01 — Requirement matrix, threat model and architecture decision

```yaml
slice_id: S150-01
profile: SECURITY_ARCHITECTURE
owner: Senior System Architect
secondary_reviewers: [ISMS-light Security Governance Expert, OWASP ASVS Local Infrastructure Expert, Security And Threat Modeling, Senior Requirement Engineer, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-150/requirement_matrix.md, documentation/arc42/09_decisions/adr-traefik-https-ingress-existing-ca.adoc, documentation/arc42/05_building_blocks.adoc, documentation/arc42/06_runtime_view.adoc]
affected_modules: [Traefik ingress, admin surface, security governance]
affected_contracts: [GUI route/auth/TLS decision, exposure boundary, rollback contract]
dependencies: [S123-02, S126-02, S128-02]
parallel_group: SERIAL-150
file_locks: [.tiny-swarm/evidence/issue-150/requirement_matrix.md, documentation/arc42/09_decisions/adr-traefik-https-ingress-existing-ca.adoc]
contract_locks: [traefik-admin-surface-contract, secure-route-contract]
architecture_locks: [traefik-https-ingress, no-insecure-dashboard, service-access-preservation]
quality_gates:
  targeted: [git diff --check]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: required; planned decision must not be written as implemented behavior
  adr: required review; extend existing ADR or add a complementary ADR if needed
stop_conditions: [auth/authorization ambiguity, route owner unclear, insecure exposure, secret value in evidence, missing rollback]
```

Done: the matrix and reviewed ADR decision fix route, auth, authorization,
TLS, exposure, ownership, rollback and verification semantics.

### Slice 02 — Desired-state/configuration implementation and regression tests

```yaml
slice_id: S150-02
profile: FULL_PATH
owner: Senior Python Automation Developer
secondary_reviewers: [Senior System Architect, Security And Threat Modeling, Senior Tester, Senior DevOps]
affected_files: [infra/config/compose/traefik/docker-compose.yml, infra/config/compose/traefik/dynamic/tls.yml, src/tiny_swarm_world/domain/ingress/desired_state.py, src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py, tests/domain/ingress/test_desired_state.py, tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py, tests/integration/test_optional_service_routing.py]
affected_modules: [Traefik compose config, ingress desired state, compose renderer, routing tests]
affected_contracts: [secure GUI route, auth/TLS secret references, no-insecure invariant, existing route contracts]
dependencies: [S150-01]
parallel_group: SERIAL-150
file_locks: [infra/config/compose/traefik/, src/tiny_swarm_world/domain/ingress/, src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py]
contract_locks: [traefik-config-contract, ingress-rendering-contract]
architecture_locks: [domain-no-infrastructure-imports, secure-admin-route]
quality_gates:
  targeted: [PYTHONPATH=src python3 -m unittest tests.domain.ingress.test_desired_state tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml, PYTHONPATH=src python3 -m unittest tests.integration.test_optional_service_routing]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: update only after verified config/model behavior
  adr: implementation must match S150-01 decision
stop_conditions: [api.insecure, raw credential, route collision, existing service-access regression, live command in tests, secret value persistence]
```

Done: desired state and configuration produce only the approved secure path;
forbidden mode, missing references, route collisions and existing routes are
covered by deterministic tests; full local quality passes or has an explicit
blocker recorded.

### Slice 03 — Evidence contract, docs and explicit live handoff

```yaml
slice_id: S150-03
profile: FULL_PATH
owner: Senior Tester
secondary_reviewers: [Live Evidence Validation Expert, Senior Documentation Engineer, Senior System Architect, Issue Completion Auditor]
affected_files: [documentation/arc42/05_building_blocks.adoc, documentation/arc42/06_runtime_view.adoc, documentation/evidence/live-greenpath-evidence-contract.md, .tiny-swarm/evidence/issue-150/implementation_summary.md, .tiny-swarm/evidence/issue-150/test_results.md, .tiny-swarm/evidence/issue-150/acceptance_checklist.md]
affected_modules: [Traefik evidence and documentation]
affected_contracts: [no-live-default, browser/live verification state, issue evidence]
dependencies: [S150-02]
parallel_group: SERIAL-150-FINAL
file_locks: [documentation/arc42/05_building_blocks.adoc, documentation/arc42/06_runtime_view.adoc, .tiny-swarm/evidence/issue-150/]
contract_locks: [live-admin-surface-evidence]
architecture_locks: [verified-vs-planned-documentation]
quality_gates:
  targeted: [git diff --check, python3 tools/quality_gate.py quality]
  required: [python3 tools/quality_gate.py quality]
documentation:
  arc42: required and evidence-backed
  adr: record final decision reference
stop_conditions: [live success inferred from static tests, missing redaction, missing evidence is not live verified, arc42 overclaim]
```

Done: docs describe the implemented route, local evidence is complete, live and
browser verification are clearly marked not run unless explicitly authorized,
and the independent auditor reviews the full matrix.

## Dependency Graph

`S123-02 -> S128-02 -> S126-02 -> S150-01 -> S150-02 -> S150-03`

## Parallel Execution

No implementation parallelism. All slices share security/route contracts and
the admin-surface ADR. Isolated worktree required; any live/browser validation
is serialized and separately consented. Conflicts: ingress, Traefik, security,
Service Access and routing workflows. Merge strictly in order.

## Automatic Work Distribution Policy

Analyze each slice across backend, runtime, tests, documentation, quality,
architecture and security. Use real subagents or documented fallback; create
distribution/consolidation evidence. Frontend stream is not applicable. Do not
parallelize route/auth/secret/ADR decisions or overlapping compose/model files.

## Git Worktree Execution Rule

Use isolated worktree `feature/issue-150-secure-traefik-gui-20260812`. No worker
may run compose, Swarm or live browser commands by default. Codex owns
consolidation, final tests and evidence.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/issue-150/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-150/`.
- Required evidence files: matrix, implementation summary, changed files,
  test results, remaining risks and acceptance checklist.
- Requirement Lead review: S150-01 and final.
- System Architect Reviewer review: all slices and final.
- Test / Evidence Reviewer review: S150-02/S150-03 and final.
- Issue Completion Auditor review: required before `DONE`.
- DONE blocking rule: any open security, route, test or evidence requirement
  forces `INCOMPLETE`, `BLOCKED` or `FAILED`.

## Quality, Documentation and Handoff

Run targeted tests first, then `python3 tools/quality_gate.py quality` and
`git diff --check` inside WSL/Linux. Never claim live/browser/Sonar success from
local checks. Handoff to #124 includes final route/auth/TLS requirement IDs,
changed files and tests. Handoff to #125 includes required live evidence fields.

Definition of Done: approved secure route is implemented and tested, insecure
mode and secret exposure are impossible in the declared surface, Service Access
is preserved, docs/evidence are synchronized and the auditor returns `PASS`.

Arc42 Check Status: existing Traefik HTTPS ADR, building blocks and runtime
view reviewed; update only from verified S150-02 behavior.

## Scope

Only the approved Traefik dashboard route, auth/TLS desired state, associated
tests, ADR/arc42 updates and evidence handoff are in scope.

## Target Outcome

An operator-scoped HTTPS GUI route exists with approved authentication and
authorization, no insecure mode or raw secret, preserved Service Access and
explicitly classified live/browser evidence.

## Architecture Constraints

Traefik remains a deployment concern; domain models stay technology-neutral;
application services depend on ports; existing ingress/TLS/consent boundaries
and Service Access contracts remain intact.

## Python Automation Assessment

Potentially affected in desired-state validation/rendering. Any implementation
must use typed models/adapters, deterministic tests, no import-time/live side
effects and the full WSL/Linux quality gate.

## Frontend Assessment

No React frontend. Browser verification is a conditional live-evidence check of
the Traefik admin surface, not a frontend build task.

## Test Strategy

Run focused ingress desired-state, compose repository and routing tests, then
`python3 tools/quality_gate.py quality`, `git diff --check` and only separately
authorized browser/live checks.

## Resilience Requirements

Missing auth/TLS references, insecure flags, collisions or failed readiness
fail closed; rollback removes only the GUI route and preserves existing service
routes. Reconcile/update behavior must be represented in later live evidence.

## Role and Ownership Map

Architect owns S150-01/ADR; Python Automation owns desired state/rendering;
Security/ASVS/Threat Modeling own exposure/auth review; Tester owns regression
and evidence; DevOps reviews deployment safety; Auditor decides completion.

## Commit and Push Plan

One issue-scoped implementation commit per slice on the feature branch after
targeted/full quality gates. No live deployment, PR merge or secret mutation is
implied by this workflow.

## Handoff to workflow execute

Promote only after #123/#126/#128 evidence and S3D locks are verified. S150-02
cannot begin without the approved S150-01 route/auth decision.

## Arc42 Check Status

Existing Traefik HTTPS ADR, building blocks and runtime view are the required
architecture sources; implementation updates must be evidence-backed.
