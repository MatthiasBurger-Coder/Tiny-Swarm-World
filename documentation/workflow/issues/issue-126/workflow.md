# Workflow: Issue #126 — OWASP ASVS and Admin-Surface Model

Workflow id: `issue-126-owasp-asvs-admin-surface-20260812`

Issue: [#126](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/126)

Authoring branch: `docs/workflow-public-beta-roadmap-20260812`

Planned execution branch: `docs/issue-126-owasp-asvs-admin-surface-20260812`

Status: `AUTHORED_INDEXED`

## Executive Summary

Map the applicable OWASP ASVS areas to Tiny Swarm World's local infrastructure
and administrative surfaces and define the admin-surface/RBAC and Service
Access threat model needed before #150. This is a scoped local-infrastructure
mapping, not a web-application certification claim.

## Requirement Clarification Gate

- Original request: execute #126 before enabling the Traefik GUI.
- Interpreted intent: create the three required security documents, classify
  applicability and establish authentication, authorization, logging,
  transport, data-protection and secret-handling expectations for all listed
  surfaces.
- Change type: security architecture/governance documentation.
- Affected process strand: surface -> threat/control -> evidence -> secure
  feature decision.
- Affected architecture area: CLI consent, compose assets, Traefik, service
  stacks, Infisical, Service Access and evidence.
- Explicit requirements: map V1/V2/V3/V4/V5/V6/V7/V8/V9/V10/V12/V13/V14;
  cover the listed surfaces and status categories applicable, partially
  applicable, not applicable and future.
- Implicit requirements: do not force unrelated web-app requirements onto
  local infrastructure; link #123 risks and #121 evidence; protect #150 route
  and credential decisions.
- Assumptions: #123 and #128 provide security/merge context; current Traefik
  ADR is the canonical path under `documentation/arc42/09_decisions/`.
- Non-goals: active scans, live commands, real secrets, ASVS certification and
  runtime changes in the mapping slice.
- Risks: misclassifying admin surfaces, vague auth ownership or unsupported
  control claims.
- Open/blocking questions: exact #150 route/auth is intentionally a downstream
  architecture decision; mapping must mark unresolved decisions as open/future.
- Confidence: 91%.
- Decision: `READY_FOR_WORKFLOW`.

## Target Picture

```text
ASVS applicability -> admin surface/RBAC model -> Service Access threat model
                                             |
                                             v
                                  secure Traefik GUI decision gate
```

## Verified Baseline, Scope and Assessments

The three required mapping files are absent. Existing routing, secret and
Traefik ADR/tests are evidence inputs, not proof of live security. Python is
not required unless implementation changes emerge; frontend is not applicable.
Resilience means unresolved/future controls stay open and no admin exposure is
accepted without transport/auth/authorization evidence.

## Ordered Slices

### Slice 01 — Matrix, surface inventory and applicability rules

```yaml
slice_id: S126-01
profile: SECURITY_ARCHITECTURE
owner: Senior System Architect
secondary_reviewers: [OWASP ASVS Local Infrastructure Expert, ISMS-light Security Governance Expert, Security And Threat Modeling, Senior Requirement Engineer]
affected_files: [.tiny-swarm/evidence/issue-126/requirement_matrix.md, documentation/arc42/09_decisions/adr-traefik-https-ingress-existing-ca.adoc]
affected_modules: [admin-surface governance, Traefik ingress]
affected_contracts: [ASVS applicability status, admin-surface inventory]
dependencies: [S123-02, S128-02]
parallel_group: SERIAL-126
file_locks: [.tiny-swarm/evidence/issue-126/requirement_matrix.md]
contract_locks: [asvs-applicability-contract, admin-surface-contract]
architecture_locks: [traefik-https-ingress, local-admin-boundary]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: required review of context, deployment and decisions
  adr: update only if the verified admin-surface decision changes
stop_conditions: [unclear ownership, insecure exposure proposal, ASVS web-app overreach, secret-bearing evidence]
```

Done: all required ASVS areas/surfaces have stable requirements and explicit
status/owner/evidence fields.

### Slice 02 — Mapping, RBAC model and threat model

```yaml
slice_id: S126-02
profile: SECURITY_ARCHITECTURE
owner: OWASP ASVS Local Infrastructure Expert
secondary_reviewers: [ISMS-light Security Governance Expert, Security And Threat Modeling, Senior Documentation Engineer, Senior Tester]
affected_files: [documentation/security/owasp-asvs-mapping.md, documentation/security/admin-surface-rbac.md, documentation/security/service-access-threat-model.md]
affected_modules: [ASVS mapping, admin surfaces, Service Access]
affected_contracts: [ASVS matrix, RBAC expectations, threat model]
dependencies: [S126-01]
parallel_group: SERIAL-126
file_locks: [documentation/security/owasp-asvs-mapping.md, documentation/security/admin-surface-rbac.md, documentation/security/service-access-threat-model.md]
contract_locks: [asvs-mapping-contract, admin-rbac-contract, threat-model-contract]
architecture_locks: [secure-admin-surface]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: synchronize verified admin-surface/ingress decision references
  adr: record reviewed/no-new-ADR or required #150 decision
stop_conditions: [certification claim, missing surface, auth/authorization ambiguity, route ownership conflict]
```

Done: required mappings and threat model are complete, scoped, redacted and
provide explicit inputs to #150.

## Dependency Graph

`S123-02 -> S128-02 -> S126-01 -> S126-02`

## Parallel Execution

Implementation is serialized because ASVS status and admin-surface ownership
feed #150. Read-only control review may parallelize after S126-01. Isolated
worktree required; no live validation. Conflicts: security/route changes.

## Automatic Work Distribution Policy

Use standard distribution/consolidation evidence. Security, architecture,
documentation and test reviewers may advise in parallel only with disjoint
locks. Do not parallelize route ownership, auth model, secret handling or ADR
decisions.

## Git Worktree Execution Rule

Use isolated worktree `docs/issue-126-owasp-asvs-admin-surface-20260812`; verify
#123/#128 evidence and current ADR path before writing.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/issue-126/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-126/`.
- Required evidence files: matrix, implementation summary, changed files,
  test results, remaining risks and acceptance checklist.
- Requirement Lead review: S126-01 and final.
- System Architect Reviewer review: S126-01/S126-02 and final.
- Test / Evidence Reviewer review: S126-02 and final.
- Issue Completion Auditor review: required before `DONE`.
- DONE blocking rule: open or unverified security/control requirement forces
  `INCOMPLETE`, `BLOCKED` or `FAILED`.

## Quality, Documentation and Handoff

Run `git diff --check`; add route/config tests only if this issue changes
executable behavior. No live security scan is implied. Handoff to #150 must
include applicable controls, admin-surface owner, auth/authorization
expectations, TLS boundary, threat scenarios, residual risks and ADR status.

Definition of Done: all required ASVS areas/surfaces are mapped, admin/RBAC and
Service Access threats are explicit, and no unresolved decision is hidden.

Arc42 Check Status: current context/deployment/Traefik ADR reviewed; update only
for verified architecture decision changes.

## Scope

Only ASVS applicability, admin/RBAC expectations, Service Access threat model
and required architecture references are in scope.

## Target Outcome

#150 has a bounded, reviewable security decision space for auth, authorization,
TLS, logging, data protection and secret handling.

## Architecture Constraints

Use local-infrastructure applicability, preserve Traefik HTTPS and do not
introduce a new service or web-application security model by analogy.

## Python Automation Assessment

Documentation-only by default; route/config behavior changes require Python
automation and deterministic test review in a separate implementation slice.

## Frontend Assessment

No React frontend; the admin surface is a deployment/routing concern with
conditional browser verification.

## Test Strategy

Check every required ASVS area/surface, applicability state, owner, gap,
evidence and `git diff --check`.

## Resilience Requirements

Future/open controls and unresolved auth/route ownership remain blockers; no
admin exposure is accepted without transport and authorization evidence.

## Role and Ownership Map

ASVS expert owns mapping; ISMS expert owns risk treatment; Threat Modeler owns
scenarios; Architect owns ADR/route boundary; Tester verifies coverage;
Requirement Lead and Auditor control completion.

## Commit and Push Plan

One issue-scoped security-documentation commit after #123/#128 review; no active
scan, live command, secret or certification claim.

## Handoff to workflow execute

Promote only with #123/#128 evidence and a complete matrix; pass the approved
admin-surface, auth/TLS and residual-risk decisions to #150.

## Arc42 Check Status

Context, deployment and Traefik decision references were reviewed; update only
verified architecture decisions.
