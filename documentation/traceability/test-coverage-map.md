# Test and Quality Coverage Map

This map identifies current check owners. A test source existing is not a pass;
results must identify the executed revision, command, environment and skips.
The former #150 figures (1761 tests, 28 skips, 622 typed files) are historical
reported figures whose original checkout-local result file is unavailable in
this checkout. They are not current verification evidence.

| Requirement IDs | Area | Current test/check path | What it protects | Evidence rule |
|---|---|---|---|---|
| REQ-124-06, REQ-124-20 | Verification policy | `tools/check_verification_policy_consistency.py` | Local/live/external state semantics | Record the executed policy check. |
| REQ-124-05, REQ-124-09 | Complexity, style and architecture | `tools/quality_gate.py quality`; `.importlinter`; `tests/architecture/test_hexagonal_imports.py` | Reviewed complexity and dependency direction | Record every required stage; source presence alone is not a pass. |
| REQ-124-05 | Python typing | `tools/quality_gate.py typecheck` | Typed source/test contracts | Counts belong to the executed candidate. |
| REQ-124-05 | Full regression | `tools/quality_gate.py test` | Repository behavior | Report actual tests, failures and skips for that run. |
| REQ-124-15, REQ-124-16 | Traefik compose | `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py` | Routing, secrets and forbidden insecure mode | Deterministic test evidence only. |
| REQ-124-08, REQ-124-16 | Composition | `tests/infrastructure/test_composition.py` | Secret-name propagation and wiring | Deterministic test evidence only. |
| REQ-124-15, REQ-124-17 | Installer | `tests/test_install_script.py` | Installer boundary | Static/mocked evidence only. |
| REQ-124-17 | Secret manifest | `tests/application/services/deployment/test_secret_management.py` | External secret classification | Static/mocked evidence only. |
| REQ-124-10, REQ-124-17 | Hygiene | `tests/architecture/test_repository_hygiene.py` | Placeholder and configuration contracts | Deterministic test evidence only. |
| REQ-124-21, REQ-124-22 | Browser/live | `tests/e2e/classic/test_post_install_browser_live.py` | Conditional authenticated service access | Separately consented live evidence, with skips reported. |
| REQ-124-21 | Installation/lifecycle | `tools/live/run_classic_acceptance.py` | Install, reconcile, update and recovery | Protected target-specific evidence; not a default development command. |
| REQ-124-23 | Sonar/external | `.github/workflows/sonar_external_gate.yml` | Candidate-specific external gate | Observe actual analyzed SHA and gate result. |

Dated qualification sources are the [RC1 candidate matrix](../release/rc1-candidate-evidence.md)
and [Issue #363 final validation](../evidence/issue-363-final-validation-20261003.md).
Neither substitutes for local or live verification of later changes. The
[documentation correction review](../audit/documentation-currency-review-20261010.md)
records checks executed for this documentation task.
