# Issue #358 test results

- `PYTHONPATH=src python3 -m unittest tests.test_package_entrypoint tests.test_classic_update_cli tests.application.services.platform.host.test_prepare_with_preflight`: PASS, 78 tests after frozen command and consent coverage.
- `python3 tools/quality_gate.py arch-lint`: PASS, six contracts kept.
- `python3 tools/quality_gate.py arch-tests`: PASS, 30 tests.
- `python3 tools/quality_gate.py typecheck`: PASS, 712 source files including package CLI files after target update.
- `git diff --check`: PASS.
- `python3 tools/quality_gate.py quality`: PASS on final tree. Verification policy, lint, arch-lint, arch-tests, typecheck and test passed; test stage ran 2,275 tests with 18 skipped.
- The first revised full run failed two tests. `test_governing_hash_cache_matches_repository_files` detected a temporary `QUALITY.md` edit, which was removed; its isolated rerun passed. The next full run failed only `test_forwarding_script_recovers_on_retry_after_bridge_appears` with return code 141. Its fake `sed` exited without reading from the fake `ip` producer, causing a scheduling-dependent SIGPIPE under `pipefail`. The fixture now drains input; its isolated rerun and final full gate passed.

No live infrastructure commands were run.
