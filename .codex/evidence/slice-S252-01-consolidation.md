# Issue #252 — S252-01 Consolidation

- Workflow: `issue-252-classic-public-beta-rc1-20260814`
- Slice: `S252-01` — Requirement, service and asset baseline; Three-Amigos gate
- Branch: `docs/workflow-issue-252-classic-public-beta-20260814`
- Real subagents: unavailable in the current tool surface
- Fallback review: complete; Codex is the final integration owner
- Result: `S252-01_READY_FOR_S252-02`

## Accepted stream results

| Stream / role | Result |
|---|---|
| Senior Requirement Engineer | Accepted all 44 matrix rows and explicit open/base-lined statuses. |
| Senior System Architect | Accepted the existing Linux/WSL2, Incus/LXC, Docker and Swarm boundary and found no authorized runtime replacement. |
| Senior Python Automation Developer | Accepted reuse of existing CLI/tool contracts and no product implementation change in this slice. |
| Senior Tester | Accepted `tests/e2e/classic/` as the canonical target and the no-duplicate migration rule. |
| Senior DevOps Engineer | Accepted the nine selected service-access stacks as RC1-required and live operations as consent-gated. |
| Senior Live Evidence Validator | Accepted host-separated, redacted, fail-closed scenario requirements; no live result was inferred. |
| Senior Documentation Engineer | Accepted planned-versus-observed separation and ignored local evidence boundaries. |
| Senior Execution Orchestrator | Accepted 12-slice metadata, acyclic dependencies and serial S252-01 handoff. |

## Findings

- The generic tracked `.codex/evidence/slice-01-*` names belong to Issue #188;
  issue-specific `slice-S252-01-*` names were used to avoid overwriting prior
  evidence.
- The selected `service-access` profile currently resolves to nine stack
  contracts: service-access, portainer, traefik, nexus, jenkins, pulsar,
  sonarqube, swagger and infisical. They are classified `RC1_REQUIRED`.
- `vaultwarden` is an existing integration asset but is not selected by the
  current Classic profile and is explicitly `NOT_IN_CLASSIC_PROFILE`.
- Reconcile is an explicit `platform reconcile --live` command. No separate
  update CLI exists; the later update scenarios must use a controlled,
  idempotent `setup run --live` rerun and evidence the change boundary.
- No live, browser, credential, Incus, Docker, Swarm, network or Administrator
  PowerShell operation ran.

## Checks

- S3 branch/status/ref check — PASS before evidence writes.
- S3D metadata/dependency check — PASS; 12 unique blocks, zero unknown
  dependencies, acyclic graph.
- `python3 tools/check_verification_policy_consistency.py` through WSL — PASS.
- Focused WSL unittest selection — PASS; 26 tests.
- `git diff --check` — PASS.
- Full WSL quality gate — PASS before execution evidence; 1,763 tests passed,
  28 skipped, with lint, architecture and mypy checks passing.
- Live/external/browser/SonarQube checks — NOT RUN; consent/applicability is
  absent for this local gate.

## Handoff

The materialized matrix, service inventory and Three-Amigos record are present
and redacted. S252-02 may proceed with the canonical test-layout migration.
The issue remains `INCOMPLETE`; no RC1 decision is permitted.
