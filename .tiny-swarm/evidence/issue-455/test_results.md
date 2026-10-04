# Issue #455 local test results

- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest
  tests.test_incus_preparation tests.test_prepare_linux tests.test_ubuntu_prerequisites
  tests.test_ubuntu_bootstrap_integration: PASS, 84 tests in 6.976s;
  /tmp/issue-455-focused-final.log (before final client-state isolation argv refinement).
- Final Incus focused suite: PASS, 29 tests in 3.288s; /tmp/issue-455-incus-final.log.
- Independent Tester: Incus + both architecture suites PASS, 72 tests in 28.166s;
  verifies address-lifetime remediation and strict composition/root boundaries.
- Required python3 tools/quality_gate.py quality: PASS, observed process exit 0;
  /tmp/issue-455-quality-verified.log. Seven stages passed: verification-policy,
  complexity (290 modules), lint, arch-lint (7 contracts), arch-tests (43 tests),
  typecheck (768 source files), test (2450 tests in 280.421s, 18 skips).
- Final-source focused suite after client-state argv refinement: PASS, 84 tests
  in 6.942s, observed process exit 0; /tmp/issue-455-focused-verified.log.
- Final full gate on unchanged final source: PASS, observed session20032 exit 0;
  /tmp/issue-455-quality-complete.log. All seven phases passed: verification-policy,
  complexity (290 modules), lint, arch-lint (7 contracts), arch-tests (43 tests in
  24.956s), typecheck (768 source files), test (2450 tests in 274.554s, 18 skips).
  No source changes followed its start. Skips are not passes or live evidence.
- git diff --check; bash -n prepare_linux.sh tools/ubuntu_python_prerequisites.sh:
  PASS after final facade/doc updates.

Intermediate failures were repaired without lowering guards: test fixture scope and
help capitalization; typed variable-width argv annotations; excess native composition
fanout; newly registered root entrypoint and removal of a reverse composition import.
Independent review also repaired mutation-time consent drift and volatile address
lifetime fingerprints. Earlier unsuccessful full-gate logs remain /tmp/issue-455-quality.log
and /tmp/issue-455-quality-final.log. Final complete gate must run on final source.

No real Incus/systemd/group/APT/Docker/network mutation or live verification.

Publication preflight: focused Incus/Linux/bootstrap regression command rerun unchanged; PASS, 84 tests in 9.482s, exit 0. git diff --check PASS.
