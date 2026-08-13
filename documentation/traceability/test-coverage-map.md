# Test and Quality Coverage Map

This map distinguishes deterministic repository checks from live acceptance.
Test names and paths below were inspected in the current branch.

| Area | Test/check path | What it protects | Result/state |
|---|---|---|---|
| Verification policy | `tools/check_verification_policy_consistency.py` | local/live/external state semantics | PASS |
| Python style | `tools/quality_gate.py quality` / Ruff | source and test lint | PASS |
| Hexagonal imports | `.importlinter`; `tests/architecture/test_hexagonal_imports.py` | dependency direction | PASS |
| Python typing | `tools/quality_gate.py quality` / Mypy | typed source/test contracts | PASS, 622 files |
| Full regression | `tools/quality_gate.py quality` | repository behavior | PASS, 1760 tests, 28 skipped |
| Traefik compose contract | `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py` | route, secret and forbidden insecure mode | PASS in #150 targeted set |
| Composition contract | `tests/infrastructure/test_composition.py` | operator secret-name propagation | PASS in #150 targeted set |
| Installer contract | `tests/test_install_script.py` | value-free default secret export | PASS in #150 targeted set |
| Secret manifest | `tests/application/services/deployment/test_secret_management.py` | external secret classification | PASS in #150 targeted set |
| Repository hygiene | `tests/architecture/test_repository_hygiene.py` | `.env.example` contract coverage | PASS in #150 targeted set |
| Browser/live | `tests/live/test_post_install_browser_live.py` | conditional live admin/service access | applicable but not executed | LIVE_CONSENT_MISSING |
| Clean-host install | canonical command in verification policy | install/Incus/Swarm/service readiness | not executed | LIVE_CONSENT_MISSING |
| SonarQube/external gate | external system | external quality result | not accessed | EXTERNAL_GATE_UNAVAILABLE |

The full quality result is recorded in
[`#150 test results`](../../.tiny-swarm/evidence/issue-150/test_results.md)
and remains local evidence only.
