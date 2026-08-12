# Workflow: Issue #123 — ISMS-light Documentation

Workflow id: `issue-123-isms-light-20260812`

Issue: [#123](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/123)

Authoring branch: `docs/workflow-public-beta-roadmap-20260812`

Planned execution branch: `docs/issue-123-isms-light-20260812`

Status: `AUTHORED_INDEXED`

## Executive Summary

Define a lightweight information-security management structure for Tiny Swarm
World. It covers scope, assets, trust boundaries, risks, controls, incident
response, secrets and risk acceptance without claiming ISO/IEC 27001
certification. It provides the security foundation for #126 and #150.

## Requirement Clarification Gate

- Original request: implement #123 after the audit foundation.
- Interpreted intent: create the six required security documents and make
  Docker socket, local HTTP/TLS, Infisical, local env files, redaction,
  evidence, incident and admin-interface risks explicit.
- Change type: security governance documentation.
- Affected process strand: asset/surface -> risk -> control -> incident/CAPA ->
  evidence/risk acceptance.
- Affected architecture area: local operator environment, Swarm/Traefik,
  service stacks, Infisical and provider interactions; no new service boundary.
- Explicit requirements: create `isms-scope.md`, `risk-register.md`,
  `statement-of-applicability.md`, `security-controls.md`,
  `incident-response.md`, `secret-handling-policy.md`; assess the listed
  surfaces and incident scenarios.
- Implicit requirements: no real secrets; controls map to #121 evidence and
  later ASVS; residual risk has an owner and treatment.
- Assumptions: local-only scope remains authoritative and #121 evidence paths
  exist or are marked planned.
- Non-goals: active scans/attacks, live commands, secret introduction,
  certification and weakening fail-closed/redaction rules.
- Risks: unreviewed residual risk, false control claims and exposure of raw
  credentials in examples.
- Open/blocking questions: no blocker for documentation authoring; route/auth
  details for #150 are deliberately deferred to #126/#150.
- Confidence: 93%.
- Decision: `READY_FOR_WORKFLOW`.

## Target Picture

```text
scope/assets/trust boundaries -> risk register -> controls/SoA
                                      |
                                      v
                         incident response + secret policy
```

## Verified Baseline, Scope and Assessments

The six ISMS files are absent; supply-chain policy files from closed #127 are
present. Scope is documentation and direct links only. Python and frontend are
not applicable. Resilience requires incident handling for secret leakage,
compromise, failed live setup and exposed admin interfaces, with recovery and
evidence states explicit. Security review must use redacted evidence and never
invent deployed controls.

## Ordered Slices

### Slice 01 — Security requirement matrix and threat boundary

```yaml
slice_id: S123-01
profile: SECURITY_GOVERNANCE
owner: Senior Requirement Engineer
secondary_reviewers: [ISMS-light Security Governance Expert, Security And Threat Modeling, Senior System Architect, Senior Tester]
affected_files: [.tiny-swarm/evidence/issue-123/requirement_matrix.md, documentation/workflow/issues/issue-123/workflow.md]
affected_modules: [ISMS governance]
affected_contracts: [security scope, risk status, residual-risk ownership]
dependencies: [S121-02]
parallel_group: SERIAL-123
file_locks: [.tiny-swarm/evidence/issue-123/requirement_matrix.md]
contract_locks: [isms-scope-contract]
architecture_locks: [local-infrastructure-trust-boundaries]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: review context, constraints and risks sections
  adr: review Traefik HTTPS ADR; no new ADR for documentation alone
stop_conditions: [unclear trust boundary, raw secret example, unsupported control claim, residual risk without owner]
```

Done: all issue surfaces/scenarios have stable requirements and owners.

### Slice 02 — ISMS documents, controls and incident model

```yaml
slice_id: S123-02
profile: SECURITY_GOVERNANCE
owner: ISMS-light Security Governance Expert
secondary_reviewers: [OWASP ASVS Local Infrastructure Expert, Security And Threat Modeling, Senior Documentation Engineer, Senior Tester]
affected_files: [documentation/security/isms-scope.md, documentation/security/risk-register.md, documentation/security/statement-of-applicability.md, documentation/security/security-controls.md, documentation/security/incident-response.md, documentation/security/secret-handling-policy.md]
affected_modules: [ISMS documentation]
affected_contracts: [risk register, SoA, security controls, incident response, secret handling]
dependencies: [S123-01]
parallel_group: SERIAL-123
file_locks: [documentation/security/isms-scope.md, documentation/security/risk-register.md, documentation/security/statement-of-applicability.md, documentation/security/security-controls.md, documentation/security/incident-response.md, documentation/security/secret-handling-policy.md]
contract_locks: [isms-documentation-contract, secret-redaction-contract]
architecture_locks: [security-boundary-and-admin-surface]
quality_gates:
  targeted: [git diff --check]
  required: []
documentation:
  arc42: synchronize only verified scope/risk statements
  adr: record reviewed ADRs and any required future decision
stop_conditions: [secret leakage, unreviewed residual risk, certification claim, weakened guard]
```

Done: all six files cover required assets, risks, controls and incidents; every
residual risk has treatment/owner/evidence state; #126 handoff is explicit.

## Dependency Graph

`S121-02 -> S123-01 -> S123-02`

## Parallel Execution

No implementation parallelism: security documents share scope, risk IDs and
secret vocabulary. Isolated worktree required; no live validation. Read-only
ASVS/threat-model review may run in parallel after S123-01. Merge sequentially.

## Automatic Work Distribution Policy

Use the standard per-slice distribution and consolidation evidence. Security,
documentation, architecture and test reviews may be separated only when write
locks are disjoint. Never parallelize secret policy, risk IDs or trust-boundary
decisions; Codex remains integration owner.

## Git Worktree Execution Rule

Use `docs/issue-123-isms-light-20260812` in an isolated worktree. Verify
predecessor #121 evidence and branch ownership before writing.

## Issue Completion Discipline

- Requirement matrix path: `.tiny-swarm/evidence/issue-123/requirement_matrix.md`.
- Required evidence path: `.tiny-swarm/evidence/issue-123/`.
- Required evidence files: matrix, implementation summary, changed files,
  test results, remaining risks and acceptance checklist.
- Requirement Lead review: S123-01 and final.
- System Architect Reviewer review: S123-01/S123-02 and final.
- Test / Evidence Reviewer review: S123-02 and final.
- Issue Completion Auditor review: required before `DONE`.
- DONE blocking rule: any open or unverified security requirement forces
  `INCOMPLETE`, `BLOCKED` or `FAILED`.

## Quality, Documentation and Handoff

Run `git diff --check`; run targeted/full Python gates only if executable
security behavior or tooling is changed. Never represent planned controls as
implemented runtime controls. Handoff to #126 includes risk IDs, control IDs,
secret policy and residual-risk states. Commit only scoped documentation and
evidence.

Definition of Done: the six files are complete, redacted, cross-linked and
independently reviewed with no unsupported security pass claim.

Arc42 Check Status: context, constraints, risks and deployment surfaces
reviewed; update only if verified scope wording changes.

## Scope

Only the six ISMS-light documents, security evidence links and directly needed
architecture references are in scope.

## Target Outcome

Security scope, risks, controls, incidents and secret handling are explicit and
ready to feed the ASVS/admin-surface decision.

## Architecture Constraints

Keep local-only trust boundaries and existing consent/redaction/hexagonal rules;
documentation cannot imply a deployed control that is not evidenced.

## Python Automation Assessment

Not applicable for the documentation slices; any security behavior/tool change
must add a separate Python/test slice and full quality gate.

## Frontend Assessment

Not applicable; admin-surface documentation is not a frontend implementation.

## Test Strategy

Validate all required risk/control/incident fields, secret-redaction wording,
links and `git diff --check`.

## Resilience Requirements

Incident response covers secret leakage, compromise, failed setup and exposed
admin surfaces with containment, recovery and evidence states.

## Role and Ownership Map

Requirement Engineer owns the matrix; ISMS expert owns scope/risks/controls;
Threat Modeler and ASVS expert review surfaces; Tester validates evidence;
Architect and Auditor provide independent decisions.

## Commit and Push Plan

One issue-scoped documentation commit after security review; no real secret,
active scan, live command or certification claim.

## Handoff to workflow execute

Promote only after #121 evidence, branch/worktree checks and a complete ISMS
matrix are present; pass control IDs and residual risks to #126.

## Arc42 Check Status

Security scope/deployment references were reviewed; update only verified
security-boundary changes.
