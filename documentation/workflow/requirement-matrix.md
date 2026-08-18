# Issue #252 Requirement Matrix Baseline

Source: https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/252

Workflow: issue-252-classic-public-beta-rc1-20260818

Status at authoring: OPEN_FOR_EXECUTION

The execution matrix must be materialized at
.tiny-swarm/evidence/issue-252/requirement_matrix.md in S252-01. It must add
exact implementation/evidence paths and results. No row may be silently deleted
or marked complete from static workflow text.

| ID | Requirement | Type | Planned slice/evidence | Verification | Status |
|---|---|---|---|---|---|
| REQ-252-001 | Qualify Classic for Public Beta RC1 on current main. | release | S04-S12 bundles | final audit | OPEN |
| REQ-252-002 | Preserve Linux/WSL2 -> Incus/LXC -> Docker -> Swarm path. | architecture | existing contracts + host evidence | architecture/live review | OPEN |
| REQ-252-003 | Exclude Podman, Kubernetes and multi-runtime work. | scope | workflow locks | changed-file review | OPEN |
| REQ-252-004 | Execute Fresh Install. | functional | RC1-S03 and RC1-S10 | live evidence | OPEN |
| REQ-252-005 | Execute post-install acceptance. | functional | RC1-S04 | canonical suite | OPEN |
| REQ-252-006 | Execute Re-run/Reconcile. | functional | RC1-S05 and RC1-S11 | no-drift evidence | OPEN |
| REQ-252-007 | Execute post-reconcile acceptance. | functional | RC1-S05 and RC1-S11 | service acceptance | OPEN |
| REQ-252-008 | Execute Update. | functional | RC1-S06 and RC1-S12 | update evidence | OPEN |
| REQ-252-009 | Execute post-update acceptance. | functional | RC1-S06 and RC1-S12 | readiness/browser/API | OPEN |
| REQ-252-010 | Cover Failure/Recovery. | resilience | RC1-S07/S08 | failure/recovery evidence | OPEN |
| REQ-252-011 | Cover restart resilience. | resilience | RC1-S09 | restart evidence | OPEN |
| REQ-252-012 | Keep tools for utilities/diagnostics/recovery/runners. | architecture | S01/S02 inventory | source review | OPEN |
| REQ-252-013 | Keep assertion-heavy acceptance tests under tests/. | testability | S02/S03 | test layout review | OPEN |
| REQ-252-014 | Classify every named asset using the six allowed labels. | governance | S01 inventory | Requirement review | OPEN |
| REQ-252-015 | Reuse or migrate existing integration browser test; no duplicate framework. | testability | S02 | canonical-suite review | OPEN |
| REQ-252-016 | Create Three-Amigos decision before live execution. | governance | S01 evidence | four-role review | OPEN |
| REQ-252-017 | Record environments, scenarios, services, transitions, timeouts, evidence, stops, severity and decision. | governance | Three-Amigos record | completeness review | OPEN |
| REQ-252-018 | Derive and classify every current Classic service. | functional | service inventory | config comparison | OPEN |
| REQ-252-019 | Document sufficient prerequisites. | functional | preflight/inventory | S01/S02/S03/S10 | OPEN |
| REQ-252-020 | Missing prerequisites fail early with remediation. | resilience | deterministic/live tests | RC1-S07 | OPEN |
| REQ-252-021 | Fresh install needs no undocumented manual repair. | functional | fresh-install runs | RC1-S03/S10 | OPEN |
| REQ-252-022 | Expected Incus/LXC topology is created. | runtime | host evidence | fresh-install review | OPEN |
| REQ-252-023 | Docker is ready on every required node. | runtime | node/Docker evidence | fresh-install review | OPEN |
| REQ-252-024 | Swarm manager/worker topology is correct and Ready/Active. | runtime | Swarm evidence | fresh-install review | OPEN |
| REQ-252-025 | Routing and Service Access become ready in order. | runtime | phase/readiness evidence | service matrix | OPEN |
| REQ-252-026 | Secrets/Infisical work without leakage. | security | redacted service evidence | redaction audit | OPEN |
| REQ-252-027 | Nexus/artifacts/registry are ready. | runtime | artifact evidence | phase checks | OPEN |
| REQ-252-028 | Jenkins, SonarQube, Pulsar, Swagger and every required service are ready. | runtime | required-service matrix | final audit | OPEN |
| REQ-252-029 | Re-run has no duplicates or unintended destruction. | resilience | reconcile comparison | RC1-S05/S11 | OPEN |
| REQ-252-030 | Update preserves healthy unrelated state and converges. | resilience | update/rollback evidence | RC1-S06/S12 | OPEN |
| REQ-252-031 | Failures are actionable/evidenced; non-success states are not passes. | release | defect/state records | final audit | OPEN |
| REQ-252-032 | Each scenario has all required fields. | quality | scenario bundles | schema audit | OPEN |
| REQ-252-033 | Local quality/preflight baseline is executed honestly. | quality | S03 evidence | QUALITY.md commands | OPEN |
| REQ-252-034 | WSL2 pre-live diagnostics execute or are blocked explicitly. | live | RC1-S02 | command/evidence review | OPEN |
| REQ-252-035 | WSL2 Fresh/Reconcile/Update and acceptance are green for RC1. | live | RC1-S03-S06 | final audit | OPEN |
| REQ-252-036 | Native Linux Fresh/Reconcile/Update and acceptance are green for RC1. | live | RC1-S10-S12 | final audit | OPEN |
| REQ-252-037 | Prerequisite, partial, recovery and restart scenarios pass or remain non-passed. | resilience | RC1-S07-S09 | final audit | OPEN |
| REQ-252-038 | Blocker/major defects have root-cause handling or explicit blocker plus regression. | release | S11 defect package | rerun/test evidence | OPEN |
| REQ-252-039 | Evidence records commit, host, time, state, readiness, exit, files, redaction and defects. | evidence | run bundles | evidence audit | OPEN |
| REQ-252-040 | No raw passwords, tokens, join tokens, auth headers, env files or sensitive output. | security | redaction/checksum | redaction review | OPEN |
| REQ-252-041 | Final gates include quality, both host matrices, services, browser/API, recovery and evidence. | release | S12 checklist | independent audit | OPEN |
| REQ-252-042 | Final decision is exactly RC1_ACCEPTED, RC1_REJECTED_BLOCKERS or RC1_REJECTED_EVIDENCE_INCOMPLETE. | release | final decision record | auditor review | OPEN |
| REQ-252-043 | RC1_ACCEPTED is forbidden with any required non-success scenario. | safety | decision guard | final audit | OPEN |
| REQ-252-044 | Project checks remain Linux/WSL; workflow does not grant admin PowerShell access. | operating constraint | workflow/branch rules | command review | OPEN |
| REQ-252-045 | PR and push events execute the locked Python quality gate through `python-quality-gate.yml`. | quality-gate | S252-13 / CI run evidence | real PR/push run | OPEN |
| REQ-252-046 | Supported Python versions run through a Conda compatibility matrix. | compatibility | S252-14 / CI run evidence | every matrix entry | OPEN |
| REQ-252-047 | `sonar_check.yml` has one explicit external-gate responsibility and missing status is not green. | quality-gate | S252-13 / Sonar evidence | real external status | OPEN |
| REQ-252-048 | Classic live automation uses schedule/manual dispatch and a verified self-hosted runner strategy. | live/CI | S252-15 / runner evidence | real workflow run | OPEN |
| REQ-252-049 | Failed, skipped, blocked, unauthorized, unavailable or unverified CI paths cannot aggregate to RC1 success. | safety/release | S252-16 / final audit | failure-semantic evidence | OPEN |
| REQ-252-050 | CI evidence records run ID, commit, trigger, runner, duration, status, artifacts, external status, redaction and defects. | evidence | S252-16 / CI evidence bundle | schema audit | OPEN |

## Current evidence state — 2026-08-18

- `RC1-S02`: `LIVE_VERIFIED` for WSL2 diagnostics/preflight.
- `RC1-S03`: `LIVE_FAILED_AFTER_MUTATION` for the historical Fresh Install
  attempt; the later secret-provisioned idempotent recovery is not a Fresh
  Install replacement.
- `RC1-S04`: `LIVE_VERIFIED` for the redacted post-install Classic
  browser/API/E2E acceptance after recovery (`92/92`).
- `RC1-S05` through `RC1-S12`: `OPEN`; no reconcile, update, restart,
  Native-Linux or final audit result is inferred.
- `RC1-CI01` through `RC1-CI05`: `OPEN`; no real GitHub Actions, Conda,
  SonarCloud or self-hosted Classic-live runner evidence is present yet.
