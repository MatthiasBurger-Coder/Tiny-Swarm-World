# Requirement Matrix: #285 / CRED-07

The issue requires observed live acceptance in two environments. This initial
matrix records the complete scope before any mutating command. Requirements
that need an approved target or live run remain `BLOCKED`, never inferred from
local tests or tool availability.

| ID | Requirement | Type | Implementation/evidence target | Verification | Status |
|---|---|---|---|---|---|
| CRED-07-REQ-001 | WSL2 checkout under `/mnt/<drive>` is exercised with a fresh install. | live | WSL2 run bundle | redacted installer result | BLOCKED |
| CRED-07-REQ-002 | WSL2 standard internal-test path is supported. | live | WSL2 preflight and install | observed preflight/install state | BLOCKED |
| CRED-07-REQ-003 | Native Linux fresh install is exercised. | live | native-Linux target run bundle | redacted installer result | BLOCKED |
| CRED-07-REQ-004 | Portainer login succeeds in each applicable environment. | live/auth | service smoke evidence | redacted authentication result | BLOCKED |
| CRED-07-REQ-005 | Infisical bootstrap/login succeeds in each applicable environment. | live/auth | service smoke evidence | redacted authentication result | BLOCKED |
| CRED-07-REQ-006 | Other catalog human-facing services are checked where feasible. | live/auth | service acceptance matrix | redacted UI/API results | BLOCKED |
| CRED-07-REQ-007 | Post-install service/UI/API acceptance is recorded. | live | service smoke checklist | observed endpoints/results | BLOCKED |
| CRED-07-REQ-008 | Rerun/reconcile does not cause credential drift. | live | rerun/reconcile bundle | before/after source metadata and auth result | BLOCKED |
| CRED-07-REQ-009 | Environment recreation resolves deterministic defaults again. | live | recreation bundle | redacted source/value-equivalence result | BLOCKED |
| CRED-07-REQ-010 | A supported custom or Infisical override replaces the default. | live/auth | protected override run | source metadata and auth result | BLOCKED |
| CRED-07-REQ-011 | Restart/recovery relevant to credential consumption is exercised. | live | restart/recovery bundle | redacted service/auth result | BLOCKED |
| CRED-07-REQ-012 | Update is tested only if a canonical update workflow exists. | applicability | CLI workflow inspection | no canonical `update` workflow exists; `reconcile` remains distinct | NOT_APPLICABLE |
| CRED-07-REQ-013 | Evidence contains no raw passwords, tokens, or authorization headers. | security | redaction review | current evidence package contains no raw live credential material | VERIFIED |
| CRED-07-REQ-014 | Blocked/skipped/degraded scenarios are never reported as PASS. | governance | state-classification record | policy states in `preflight.md` and this audit | VERIFIED |
| CRED-07-REQ-015 | Full local quality gate is green on the final candidate. | local | quality-gate result | `python3 tools/quality_gate.py quality` | VERIFIED |
| CRED-07-REQ-016 | Final acceptance matrix maps every parent EPIC criterion to evidence. | governance | final matrix and evidence index | completion audit | BLOCKED |
| CRED-07-REQ-017 | Three-Amigos WSL2 fresh-install scenario is observed. | live | WSL2 bundle | live evidence | BLOCKED |
| CRED-07-REQ-018 | Three-Amigos native-Linux parity scenario is observed. | live | native-Linux bundle | live evidence | BLOCKED |
| CRED-07-REQ-019 | Three-Amigos rerun scenario is observed. | live | rerun bundle | live evidence | BLOCKED |
| CRED-07-REQ-020 | Three-Amigos override scenario is observed. | live | override bundle | live evidence | BLOCKED |

The issue cannot be marked complete until all live requirements have
`LIVE_VERIFIED` evidence and the final quality/review gates pass.

## Parent EPIC #277 traceability

The following parent criteria are explicitly carried into the final acceptance
scope. Existing CRED-01 through CRED-06 work supplies the implementation
baseline where noted; CRED-07 must supply the missing observed live evidence.

| Parent criterion from #277 | CRED-07 evidence mapping | Status |
|---|---|---|
| Canonical `TSW1234STW5678` default | catalog plus live login evidence | BLOCKED |
| Universal default for technically compatible human-facing services | catalog/service acceptance matrix | BLOCKED |
| Centralized deterministic alternatives for incompatible components | catalog plus feasible service checks | BLOCKED |
| Machine/bootstrap credentials need no manual preparation | fresh-install evidence | BLOCKED |
| Special-format values satisfy consumers | service/API acceptance evidence | BLOCKED |
| Random default-password generation absent from normal path | inherited CRED-04 implementation; live fresh-install result | BLOCKED |
| Random-default recovery persistence absent from normal path | inherited CRED-04 implementation; recreation result | BLOCKED |
| Reinstall/reconcile is deterministic | CRED-07-REQ-008 | BLOCKED |
| Fresh checkout installs without a password file | CRED-07-REQ-001 and REQ-003 | BLOCKED |
| WSL2 `/mnt/d` is not blocked by unnecessary credential-state permissions | CRED-07-REQ-001 and REQ-002 | BLOCKED |
| Native Linux has equivalent behavior | CRED-07-REQ-003 and REQ-018 | BLOCKED |
| Infisical override can replace defaults | CRED-07-REQ-010 and REQ-020 | BLOCKED |
| Explicit operator overrides are supported | CRED-07-REQ-010 and REQ-020 | BLOCKED |
| Self-hosted Infisical has no circular bootstrap dependency | CRED-07-REQ-005 | BLOCKED |
| Documentation marks defaults `INTERNAL/TEST ONLY` | inherited CRED-06 documentation; live output evidence | BLOCKED |
| Enterprise AD/LDAP/SSO/network/IAM boundary is external | inherited CRED-06 documentation; evidence review | VERIFIED |
| Installer output provides URL/login information | CRED-07-REQ-002 and REQ-007 | BLOCKED |
| Obsolete modes/files/abstractions are removed or isolated | inherited CRED-04/CRED-06 implementation; live smoke confirms path | BLOCKED |
| Unit/integration tests cover resolution and precedence | inherited CRED-01–CRED-06 quality evidence | VERIFIED |
| Live/E2E default logins succeed | CRED-07-REQ-004 through REQ-007 | BLOCKED |
| Live/E2E override succeeds | CRED-07-REQ-010 and REQ-020 | BLOCKED |
| Architecture/configuration documentation matches behavior | inherited CRED-01–CRED-06 evidence; live result | BLOCKED |
