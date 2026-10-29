# S449-ROUTE-8086-P1 consolidation

Status: IMPLEMENTED AND LOCALLY VERIFIED; CHECKPOINT PENDING.

The candidate retains a fixed ordered legacy source tuple, verifies complete
parent/service/port/label order and boolean types before transformation, and
produces scoped policy v2. Infisical-only drops legacy 8086 while retaining
17080; complete service-access selection transfers exactly that legacy 8086
to service-access. G2c uses the narrow P0 recomputation/validation API and G2d
requires v2. No host route, observed source, version support, persistence,
admission or live result is claimed. Legacy setup and P0a remain unchanged.

The integration-owner preflight and six-role review tuple are recorded in
distribution at checkpoint `8451e16f64839da205874ac3d17ec5de27b`.
Final independent review status and exact-source designated SSH PC WSL
verification are recorded below. No local tests or host operations were run by
this implementation stream.

## Verification and review correction

On designated SSH PC WSL Python 3.14, exact-source targeted suites passed 74
tests and direct Ruff passed. `python3 tools/quality_gate.py quality` passed
exit 0: 3,412 tests run, 37 skipped, 211.998 seconds. `git diff --check`
passed. Python 3.12 and live host execution were not tested.

Security and Architecture GO cover the final source and original test tuple;
Tester GO was rebound to the final CLI test, and Python/Requirement GO cover
the final complete candidate, according to the integration owner. DevOps GO
is reported specifically for scoped-policy SHA-256
`ca95d6cf8e305a8ab172051b520e7e4777a4b2fb1ab76ed9bfd749073361bcae`,
desired-conversion SHA-256
`b7de6c2b9cf06abbbfd5feb0eb9aad79a61cf4b61c172973fed53b6870426b3c`,
admission-service SHA-256
`394ec5c69b4e7ea5cf30b8495601739b273950c0655cb3cf9bb773613246bfc7`
and CLI-test SHA-256
`25b279bbd3715ca590dfe5826b9dc7f7009009c2bfddba20f5799bb977c86dc1`.
This does not imply a DevOps review of all seven candidate files. A Tester
review found the initial CLI
regression covered only Infisical and did not assert exit status. The final
test covers both Infisical-only and service-access with full closure, exact
BLOCKED_UNSUPPORTED JSON and exit 2, redaction and no save/host calls.

The ordered legacy source validation precedes the narrow 8086 transformation.
This is a desired policy result only: runtime source, host and ownership remain
UNKNOWN. No runtime, host route, supported version or live outcome is claimed.

## CP_RECORD

- sliceId: S449-ROUTE-8086-P1
- workflowVersion: 1.65
- sliceTitle: Versioned scoped 8086 policy and coupled consumers
- responsibleRole: Senior Python Automation Developer; root integration owner
- changedFiles: src/tiny_swarm_world/domain/lifecycle/scoped_route_policy.py,
  src/tiny_swarm_world/domain/lifecycle/desired_manifest_v2.py,
  src/tiny_swarm_world/application/services/migration_admission.py,
  tests/domain/lifecycle/test_scoped_route_policy.py,
  tests/domain/lifecycle/test_desired_manifest_v2.py,
  tests/application/services/test_migration_admission.py,
  tests/test_migration_admission_cli.py,
  .codex/evidence/slice-449-route-8086-p1-distribution.md,
  .codex/evidence/slice-449-route-8086-p1-consolidation.md
- qualityCommands: PYTHONPATH=src python3 -m unittest
  tests.domain.lifecycle.test_scoped_route_policy
  tests.domain.lifecycle.test_desired_manifest_v2
  tests.domain.lifecycle.test_legacy_route_candidate
  tests.application.services.test_migration_admission
  tests.test_migration_admission_cli tests.test_migration_preview_cli;
  direct Ruff changed code/tests; python3 tools/quality_gate.py quality;
  git diff --check
- qualityResult: PASS on designated SSH PC WSL Python 3.14; 74 targeted tests,
  Ruff, full quality exit 0, 3,412 tests run, 37 skipped, 211.998 seconds
- rollbackReference: 8451e16f64839da205874ac3d17ecb7eec5de27b
- arc42Updated: false
- adrUpdated: false
- commitSha: pending checkpoint commit
- limitations: Python 3.12 and live host execution untested. No actual source, host/ownership, runtime support or admission.
