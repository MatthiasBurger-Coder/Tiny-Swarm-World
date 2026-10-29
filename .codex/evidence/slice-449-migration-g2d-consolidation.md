# S449-MIGRATION-G2D consolidation

Status: IMPLEMENTED AND LOCALLY VERIFIED; CHECKPOINT PENDING.

This internal application use case invokes only injected read-only manifest
and catalog load ports, checks a nonempty exact-string snapshot token, derives
the desired plan internally, and calls the concrete installation-scoped G1
capability. It emits only the closed BLOCKED_UNKNOWN or BLOCKED_UNSUPPORTED
result with applied/qualified false. The empty immutable support registry is
checked; no capability injection, positive admission, host, write, CLI or
runtime composition exists in this slice.

The S3D preflight and six-role design review are recorded in distribution at
checkpoint `7decdeb9adffc39774651092543ad9b719a25005`. Final independent candidate review status and exact-source SSH PC WSL
verification are recorded below. No local test or host operation was performed
by the implementation stream. G2e remains a separately reviewed future operator
entrypoint; live host admission and support decisions are not established.

## Final verification and security correction

The integration owner reports final Architecture, Security, Tester,
Requirement, Python and DevOps GO for the source/test tuple listed in
distribution; DevOps also reports S3/S3D GO for the five task files. Earlier
six-role planning decisions and S3/S3D are separately recorded in distribution.

On designated SSH PC WSL, Python 3.14 exact-source targeted suites passed
66 tests and direct Ruff passed. `python3 tools/quality_gate.py quality`
passed exit 0: 3,398 tests run, 37 skipped, 212.755 seconds.
`git diff --check` passed. Python 3.12 and live host execution were not tested.

Security review found that merely comparing the preserved v1 snapshot did not
bind a desired plan to the request: a plan for a different listener could
reach the unsupported result. The final candidate independently checks the
request-derived P0 route/profile, stack/exposure policy and type-strict v1
snapshot before checking capability. Regressions cover a different listener,
forged profile, routes, flag types, stack, exposure, schema and snapshot; all
remain BLOCKED_UNKNOWN without invoking the classifier. This does not create
an admitted or host-safe state.

## CP_RECORD

- sliceId: S449-MIGRATION-G2D
- workflowVersion: 1.62
- sliceTitle: Fail-closed application migration admission
- responsibleRole: Senior Python Automation Developer; root integration owner
- changedFiles: src/tiny_swarm_world/application/ports/lifecycle/migration_admission.py,
  src/tiny_swarm_world/application/services/migration_admission.py,
  tests/application/services/test_migration_admission.py,
  .codex/evidence/slice-449-migration-g2d-distribution.md,
  .codex/evidence/slice-449-migration-g2d-consolidation.md
- qualityCommands: PYTHONPATH=src python3 -m unittest
  tests.application.services.test_migration_admission
  tests.domain.lifecycle.test_desired_manifest_v2
  tests.domain.lifecycle.test_scoped_route_policy
  tests.test_migration_preview_cli
  tests.infrastructure.adapters.lifecycle.test_manifest;
  direct Ruff on new port, service and tests;
  python3 tools/quality_gate.py quality; git diff --check
- qualityResult: PASS on designated SSH PC WSL Python 3.14; 66 targeted tests,
  Ruff, full quality exit 0, 3,398 tests run, 37 skipped, 212.755 seconds
- rollbackReference: 7decdeb9adffc39774651092543ad9b719a25005
- arc42Updated: false
- adrUpdated: false
- commitSha: pending checkpoint commit
- limitations: Python 3.12 and live host execution not tested; no positive
  admission, runtime/CLI wiring, ownership, supported version or host qualification. G2e remains a separately reviewed follow-on.
