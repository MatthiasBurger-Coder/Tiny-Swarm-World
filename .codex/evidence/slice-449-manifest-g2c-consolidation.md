# S449-MANIFEST-G2C consolidation

Status: IMPLEMENTED AND LOCALLY VERIFIED; CHECKPOINT PENDING.

This candidate creates a deeply detached, immutable desired-only v2 value and
conversion plan; it does not create a persisted or adopted installation,
change the v1 decoder, perform host I/O, establish runtime source or support,
or qualify a live fixture. Every actual identity and runtime source remains
UNKNOWN; applied and qualified remain false.

The conversion revalidates and snapshots v1 and catalog data before invoking
both G2a and P0 on the same detached inputs, rejects unknown model fields
before serialization, requires the exact P0 policy/algorithm and UNKNOWN
observations, and exposes fixed AUTHORITY_GAP without partial output for
invalid or unsupported data. Tests cover v1 preservation, vectors, policy
gaps, source drift, forged models, caller-supplied bindings, detached values
and no host I/O.

The integration-owner handoff and reviewed contract/workflow are recorded in
the distribution at base `d16eb1a05683398a7e3e59692cd3e294b63cfe49`.
The final source reviews and designated SSH PC WSL targeted tests, Ruff and
full quality results are recorded below and in the distribution. No local
tests or host operations were executed by this implementation stream.

## Final verification and review corrections

The integration owner reports final Security and Architecture source GO and
Tester GO rebound to the final test bytes. Requirement and Python GO covered
the final source and previous test bytes; the final test-only change added
typing casts without changing intentionally invalid runtime values. Source and
test SHA-256 values are recorded in the distribution.

On designated SSH PC WSL Python 3.14, exact-source targeted suites passed 66
tests, direct Ruff passed, and `python3 tools/quality_gate.py quality` passed
exit 0: 3,389 tests run, 37 skipped, 204.131 seconds. `git diff --check`
passed. Python 3.12 and live host execution were not tested.

Architecture and Tester reviews identified that public desired-value
construction allowed mutable input and inconsistent conversion status.
Construction was restricted to the conversion path, snapshots defensively
detached and conversion status invariants added. A subsequent Security and
Architecture review found Python's equality could equate integer flags with
booleans; the final implementation verifies exact built-in types for each
route field before equality and tests integer and subclass forgeries. An
initial full quality run found five mypy errors in deliberately invalid
test values; test-only casts fixed the annotations without altering runtime
values, and the full gate passed afterward.

## CP_RECORD

- sliceId: S449-MANIFEST-G2C
- workflowVersion: 1.61
- sliceTitle: Unadopted desired v2 conversion
- responsibleRole: Senior Python Automation Developer; root integration owner
- changedFiles: src/tiny_swarm_world/domain/lifecycle/desired_manifest_v2.py,
  tests/domain/lifecycle/test_desired_manifest_v2.py,
  .codex/evidence/slice-449-manifest-g2c-distribution.md,
  .codex/evidence/slice-449-manifest-g2c-consolidation.md
- qualityCommands: PYTHONPATH=src python3 -m unittest
  tests.domain.lifecycle.test_desired_manifest_v2
  tests.domain.lifecycle.test_manifest_v2
  tests.domain.lifecycle.test_scoped_route_policy
  tests.domain.lifecycle.test_models
  tests.infrastructure.adapters.lifecycle.test_manifest
  tests.test_migration_preview_cli;
  direct Ruff on new source and test; python3 tools/quality_gate.py quality;
  git diff --check
- qualityResult: PASS on designated SSH PC WSL Python 3.14; 66 targeted tests,
  Ruff, full quality exit 0, 3,389 tests run, 37 skipped, 204.131 seconds
- rollbackReference: d16eb1a05683398a7e3e59692cd3e294b63cfe49
- arc42Updated: false
- adrUpdated: false
- commitSha: pending checkpoint commit
- limitations: Python 3.12 and live host execution untested; desired values
  are not persisted/adopted state, runtime source evidence, ownership, host
  safety, supported-version qualification or admission.
