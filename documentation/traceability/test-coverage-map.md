# Test and Quality Coverage Map

This map distinguishes deterministic repository checks from live acceptance.
Test names and paths below were inspected in the current branch.

| Requirement IDs | Area | Test/check path | What it protects | Result/state |
|---|---|---|---|---|
| REQ-124-06, REQ-124-20 | Verification policy | `tools/check_verification_policy_consistency.py` | local/live/external state semantics | PASS |
| REQ-124-05, REQ-124-09 | Python style/architecture | `tools/quality_gate.py quality`; `.importlinter`; `tests/architecture/test_hexagonal_imports.py` | lint and dependency direction | PASS |
| REQ-124-05 | Python typing | `tools/quality_gate.py quality` / Mypy | typed source/test contracts | PASS, 622 files |
| REQ-124-05 | Full regression | `tools/quality_gate.py quality` | repository behavior | PASS, 1761 tests, 28 skipped |
| REQ-124-15, REQ-124-16 | Traefik compose contract | `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py` | route, secret, Service Access and forbidden insecure mode | PASS in #150 targeted set |
| REQ-124-08, REQ-124-16 | Composition contract | `tests/infrastructure/test_composition.py` | operator secret-name propagation and routing | PASS in #150 targeted set |
| REQ-124-15, REQ-124-17 | Installer contract | `tests/test_install_script.py` | value-free default secret export | PASS in #150 targeted set |
| REQ-124-17 | Secret manifest | `tests/application/services/deployment/test_secret_management.py` | required external secret classification/fail-closed reference | PASS in #150 targeted set |
| REQ-124-10, REQ-124-17 | Repository hygiene | `tests/architecture/test_repository_hygiene.py` | `.env.example` and value-free contract coverage | PASS in #150 targeted set |
| REQ-124-21, REQ-124-22 | Browser/live | `tests/live/test_post_install_browser_live.py` | conditional live admin/service access | LIVE_CONSENT_MISSING |
| REQ-124-21 | Clean-host install | canonical command in `documentation/process/verification-state-policy.md` | install/Incus/Swarm/service readiness | LIVE_CONSENT_MISSING |
| REQ-124-23 | SonarQube/external gate | external system | external quality result | EXTERNAL_GATE_UNAVAILABLE |

The full quality result is recorded in
[`#150 test results`](../../.tiny-swarm/evidence/issue-150/test_results.md)
and remains local evidence only.
