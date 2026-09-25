# Test results — issue #352

S352-01:
- PYTHONPATH=src python3 -m unittest tests.test_windows_wsl_bridge_assets: PASS, 11 tests, normal checkout; includes mocked Pester contract. Prior home-path prerequisite resolved without code changes.
- python3 tools/quality_gate.py arch-tests: PASS, 22 tests.
- git diff --check: PASS.
- python3 tools/quality_gate.py quality: PASS, 2099 tests, 18 skipped; all local sub-gates passed.

No live or external verification.

## S352-02

202 targeted manifest/model/renderer/composition/installer tests PASS; lint PASS; typecheck PASS (688 files); python3 tools/quality_gate.py quality PASS (2110 tests, 18 skipped); git diff --check PASS.

No live or external result is claimed.

## S352-03

Targeted unittest suite PASS: 156 tests. Final python3 tools/quality_gate.py quality PASS: 2128 tests, 18 skipped; lint/typecheck, five import contracts, 22 architecture tests and verification policy passed. Final log: /tmp/tsw352-s03-final-quality.log. git diff --check PASS. Independent architecture and test reviews ACCEPT after retry1 compatibility repairs.

No live or external result is claimed.

## S352-04

Targeted Compose suite PASS: 67 tests. python3 tools/quality_gate.py quality PASS: 2137 tests, 18 skipped; lint/typecheck, five import contracts, 22 architecture tests and verification policy passed. Log: /tmp/tsw352-s04-quality.log. git diff --check PASS. Independent architecture and test reviewers ACCEPT.

No live or external result is claimed.
