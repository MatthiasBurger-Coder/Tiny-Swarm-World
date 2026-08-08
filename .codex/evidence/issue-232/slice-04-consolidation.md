# Issue #232 — Slice 04 consolidation

- Workflow: `issue-232-20260808`
- Slice: `04` — Static artifact-contract preflight service
- Decision: ACCEPTED for checkpoint commit.
- Execution mode: serial role-based fallback; no callable Codex subagents were
  available and no live infrastructure was used.

## Implemented contract

- `PortArtifactContractInventory` separates static inventory/context inspection
  from the concrete Compose repository while preserving the application
  boundary.
- `StaticArtifactContractPreflight` validates the selected profile inventory,
  resolves only approved build-context paths through the port, and checks them
  with `PortLocalFileStorage.directory_exists()`.
- Static results are represented by the existing safe `PreflightResult`/
  `PreflightCheck` contract with mandatory severity, explicit `static` evidence
  scope, stable issue codes and remediation text.
- The setup installation plan now runs `artifact contract preflight`
  immediately after general preflight and before host/platform/artifact phases.
  A failed check stops later phases through the existing setup phase gate.
- Composition wires the static service without constructing or invoking Docker,
  HTTP, registry, Nexus or credential-bearing clients from the static path.

## Role-based review findings

| Reviewer | Decision | Evidence |
|---|---|---|
| Senior Python Automation Developer | accepted | static service and composition tests passed |
| Senior Tester | accepted | success, missing-context, safe-remediation and phase-stop tests passed |
| Senior System Architect | accepted after correction | initial direct Compose-port import violated the existing artifact boundary; `PortArtifactContractInventory` resolved it and architecture tests passed |
| Senior Requirement Engineer | accepted | REQ-007, REQ-010, REQ-013, REQ-017 and REQ-021 mapped to implementation/evidence |
| Senior DevOps / security review | accepted | static path has no live client or mutating publisher dependency |

## Verification

- Focused static/setup/preflight tests: `53` tests, `OK`.
- Compose/composition regression tests: `153` tests, `OK` after phase-order expectation update.
- Real static preflight smoke: `PASSED`, profile `service-access`, 19 contracts,
  19 required images, 0 issues.
- `python3 tools/quality_gate.py lint`: PASS.
- `python3 tools/quality_gate.py arch-tests`: PASS, 18 tests.
- `python3 tools/quality_gate.py typecheck`: PASS, no issues in 534 source files.
- `python3 tools/quality_gate.py quality`: PASS; verification policy, lint,
  architecture, typecheck and test stages all reported success. Full discovery
  reported `1,611` tests, `28 skipped`, and `OK` in 109.774 seconds.
- `git diff --check`: PASS.

## Consolidation scope

No live Docker, registry, Nexus, Incus or deployment operation was performed.
The historical global evidence file `.codex/evidence/slice-01-distribution.md`
was not modified; Slice 04 evidence remains namespaced below
`.codex/evidence/issue-232/`.
