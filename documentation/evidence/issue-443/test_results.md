# Issue #443 verification

Environment: Linux/WSL shell, Python 3.14.4. Source remains compatible with Python 3.12 syntax; a separate Python 3.12 run was not performed. Baseline SHA and working-tree scope are in implementation_summary.md/changed_files.md.

| Command | Result | Exit code | Evidence |
|---|---|---|---|
| `PYTHONPATH=src python3 -m unittest tests.test_service_selection_cli tests.test_lifecycle_cli tests.application.services.test_service_selection tests.domain.lifecycle.test_selection` | PASS: 23 tests (19 new + 4 existing lifecycle CLI) | 0 | local targeted-tests.txt |
| `python3 tools/quality_gate.py quality` | NON-PASS, superseded: registry expectation corrected; three installer tests lacked dependencies after clearing HOME; interrupted for venv rerun | 241 (SIGTERM propagated) | local quality.txt |
| `PYTHONPATH=src .venv/bin/python -m unittest tests.test_simple_installer.TestSimpleInstallerSecretBootstrap.test_main_passes_single_credential_contract_to_legacy_execution tests.test_simple_installer.TestSimpleInstallerSecretBootstrap.test_main_preserves_child_exit_and_only_prints_credentials_on_success tests.test_simple_installer.TestSimpleInstallerSecretBootstrap.test_main_reports_installer_error_without_exposing_values` | PASS: all three environment-dependent tests | 0 | local environment-tests.txt |
| `PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint.TestPackageEntrypoint.test_every_declared_workflow_keeps_its_command_name tests.test_package_entrypoint.TestPackageEntrypoint.test_every_mutating_workflow_refuses_missing_live_consent_with_exit_two` | PASS: registry and consent coverage | 0 | observed stdout |
| `.venv/bin/python tools/quality_gate.py quality` | PASS: policy, complexity (321 modules), lint, arch-lint (7 contracts), arch-tests (43 tests), typecheck (829 files), test (2680 tests, 18 skipped) | 0 | local quality-venv.txt |
| `git diff --check` | PASS | 0 | executed from repository root |

The initial complexity check flagged the enlarged CLI parser. Selection-specific validation was moved into its adapter module, preserving the guardrail; the subsequent full-gate complexity stage passed. Independent review found and verified correction of minimal-selection persistence and compatible-preset handling. No thresholds or existing tests were weakened.

Local deterministic checks only. No live infrastructure/installation/browser operation or external quality gate was executed. Required issue evidence lives in .tiny-swarm/evidence/issue-443/ with this tracked documentation mirror.

Environment diagnosis: system pydantic is installed in the user site; three installer tests replace HOME with an isolated temporary directory, making the subprocess probe lose that package. Existing project .venv keeps dependencies independently of HOME. All three pass with .venv. The first run remains NON-PASS; no product or test-environment guard was weakened. The registry contract test now explicitly includes add/remove previews and still checks every declared command.

Final full suite: 2680 tests in 631.839 seconds, OK (skipped=18). Skipped tests are not claimed as verified live/external coverage. The full gate exited 0.

## Publication security amendment

Initial PR #482 CI quality and Python 3.12/3.13/3.14 compatibility checks passed. SonarCloud run 39123277126 failed new_security_rating=C on pythonsecurity:S8707 in the selection-config path read (new-code coverage 93.1%, duplication 0%). This failed result was not bypassed.

The CLI now resolves both cwd and config strictly, requires a contained regular file before reading, and sanitizes Python 3.12 RuntimeError symlink-loop failures along with OSError. Tests reject absolute/parent/symlink escapes before read_text, accept an internal file, and verify the loop sanitizer. No scanner rules or quality thresholds changed.

Final focused command (`PYTHONPATH=src .venv/bin/python -m unittest tests.test_service_selection_cli tests.test_lifecycle_cli tests.application.services.test_service_selection tests.domain.lifecycle.test_selection`): PASS, 25 tests, exit 0 (security-regressions.txt).
Final `.venv/bin/python tools/quality_gate.py quality`: PASS, exit 0; 2682 tests in 668.249s, 18 skipped; 321 complexity modules, 7 architecture contracts, 43 architecture tests, typecheck 829 files (quality-security-final.txt). A preliminary amendment run was superseded/interrupted with exit 241 after the Python 3.12 compatibility correction; it is not a pass.

Independent amendment review: requirements/architecture/automation approve; local completion PASS. Actual current-revision SonarCloud recovery remains required before merge and is tracked in PR #482.
