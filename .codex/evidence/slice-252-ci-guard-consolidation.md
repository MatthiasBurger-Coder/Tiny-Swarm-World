# Issue #252 CI/live-runner guard slice consolidation

## Stream results

- runtime: restricted the two hosted Python workflows to `main` pushes and
  pull requests targeting `main`; made a manual live `block` input fail the
  runner qualification job; added read-only Incus/Docker capability probes.
- tests: extended the existing CI contract tests for trigger, approval and
  capability semantics.
- quality: activated `TSW_RUN_POST_INSTALL_BROWSER_LIVE=1` in the existing
  Classic runner so the canonical live browser/API class cannot be silently
  skipped.

## Accepted findings

- The changes are limited to the existing workflow, runner and contract-test
  surfaces.
- No new test framework, orchestration abstraction, live mutation or update
  command was introduced.
- YAML parsing, `git diff --check`, focused CI tests and Python compilation
  passed.
- The full repository quality gate passed: 1835 tests, 18 expected local
  skips.
- The runner consent-negative path produced `LIVE_CONSENT_MISSING`, exit 1,
  zero operations and redaction confirmation.

## Rejected findings

- No update implementation was accepted because the current CLI exposes no
  canonical `update` workflow; guessing `platform reconcile` as an update
  would violate the active workflow stop condition.
- No live result was promoted from static or historical evidence.

## Files changed

- `.github/workflows/python-quality-gate.yml`
- `.github/workflows/python-compatibility.yml`
- `.github/workflows/nightly-classic-live.yml`
- `tools/live/run_classic_acceptance.py`
- `tests/test_ci_workflow_contract.py`
- `documentation/governance/ci-quality-gates.md`

## Conflicts and integration decision

- No file or architecture conflict found.
- Live infrastructure remains serialized and was not invoked in this slice.
- Consolidation accepted for local verification; RC1 remains incomplete until
  credentialed WSL2/native-Linux lifecycle and real external workflow evidence
  exist.
