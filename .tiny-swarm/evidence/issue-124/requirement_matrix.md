# Issue #124 Requirement Matrix

`VERIFIED_LOCAL` identifies a checked repository artifact or local test. It is
not live, browser, installation, external-gate or SonarQube success. Open live
rows are intentionally carried forward to #125 and the Public-Beta gate.

| ID | Requirement | Source / implementation | Test or check | Evidence | Status |
|---|---|---|---|---|---|
| REQ-124-01 | Create a stable requirement inventory | issue #124; `documentation/traceability/requirements.md` | file/content review | this package | VERIFIED_LOCAL |
| REQ-124-02 | Map each selected requirement to architecture | issue #124; `documentation/traceability/traceability-matrix.md` | path review | matrix | VERIFIED_LOCAL |
| REQ-124-03 | Map each selected requirement to implementation/configuration | issue #124; matrix | source/config path review | matrix | VERIFIED_LOCAL |
| REQ-124-04 | Map each selected requirement to tests/checks | issue #124; `documentation/traceability/test-coverage-map.md` | test path review | coverage map | VERIFIED_LOCAL |
| REQ-124-05 | Map each selected requirement to quality gates | `QUALITY.md`; `tools/quality_gate.py` | quality command inventory | coverage map | VERIFIED_LOCAL |
| REQ-124-06 | Map live requirements without fabricating success | `documentation/process/verification-state-policy.md` | status vocabulary review | `live-evidence-map.md` | VERIFIED_LOCAL |
| REQ-124-07 | Include Linux/WSL-only operating boundary | `AGENTS.md`; arc42 deployment view | source/path review | matrix row REQ-124-07 | VERIFIED_LOCAL |
| REQ-124-08 | Include Docker Swarm-first/LXC-native architecture | `AGENTS.md`; `documentation/arc42/07_deployment_view.adoc` | architecture path review | matrix row REQ-124-08 | VERIFIED_LOCAL |
| REQ-124-09 | Include hexagonal dependency boundaries | `AGENTS.md`; `documentation/arc42/05_building_blocks.adoc` | import-linter and arch tests | `test_results.md` | VERIFIED_LOCAL |
| REQ-124-10 | Include audit evidence governance | #121; `documentation/audit/README.md` | evidence path review | #121 evidence | VERIFIED_LOCAL |
| REQ-124-11 | Include QMS controls | #122; `documentation/qms/qms-light.md` | documentation path review | #122 evidence | VERIFIED_LOCAL |
| REQ-124-12 | Include ISMS, threat and secret controls | #123; `documentation/security/` | documentation path review | #123 evidence | VERIFIED_LOCAL |
| REQ-124-13 | Include branch and CI governance | #128; `documentation/governance/` | documentation path review | #128 evidence | VERIFIED_LOCAL |
| REQ-124-14 | Include ASVS/admin-surface controls | #126; `documentation/security/owasp-asvs-mapping.md` | documentation path review | #126 evidence | VERIFIED_LOCAL |
| REQ-124-15 | Include secure Traefik dashboard behavior | #150; Traefik compose/dynamic config | targeted compose/config tests | #150 evidence | VERIFIED_LOCAL |
| REQ-124-16 | Include Service Access preservation | #150; arc42 deployment view | composition/routing regression tests | #150 test results | VERIFIED_LOCAL |
| REQ-124-17 | Include secret redaction and value-free evidence | #121/#123/#126/#150 policies | content and repository review | issue evidence packages | VERIFIED_LOCAL |
| REQ-124-18 | Include fresh install/reconcile/update live scenarios | #125 handoff; Green-Path contract | no live run authorized | `live-evidence-map.md` | LIVE_CONSENT_MISSING |
| REQ-124-19 | Include live TLS/DNS/browser evidence | #150 handoff; #125 scope | no live run authorized | `live-evidence-map.md` | LIVE_CONSENT_MISSING |
| REQ-124-20 | Include external quality-gate state | verification policy | no external result accessed | `live-evidence-map.md` | EXTERNAL_GATE_UNAVAILABLE |
| REQ-124-21 | Keep missing, blocked and refused states visible | #121 evidence policy; verification policy | status vocabulary review | all four docs | VERIFIED_LOCAL |
| REQ-124-22 | Provide handoff IDs and canonical navigation targets | #125 and #129 workflows | link/path review | matrix and maps | VERIFIED_LOCAL |

| REQ-124-23 | Include external quality-gate state | verification-state policy | no external result accessed | `live-evidence-map.md` | EXTERNAL_GATE_UNAVAILABLE |
| REQ-124-24 | Keep evidence and navigation handoffs separate and explicit | #125/#129 workflows | path/link review | matrix and maps | VERIFIED_LOCAL |

No row marked `LIVE_CONSENT_MISSING` or `EXTERNAL_GATE_UNAVAILABLE` is a pass.
