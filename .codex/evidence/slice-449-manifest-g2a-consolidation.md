# S449-MANIFEST-G2A consolidation

Status: IMPLEMENTED AND LOCALLY VERIFIED; CHECKPOINT PENDING.

This domain-only candidate revalidates schema-1 inputs from plain data, checks
catalog identity and foundation/selection relations, and creates a deeply
detached immutable compatibility preview. It produces no schema-2 manifest,
runtime caller integration, persisted migration, host admission or ownership
evidence. UNKNOWN identities remain unadopted. Existing v1 runtime models and
decoder have not been changed.

Design preflight and six role decisions are recorded in
`slice-449-manifest-g2a-distribution.md`, based on checkpoint
`4beca580bb667279549874638716eee7c049fa1d`.
The integration owner reports final exact-source Requirement, Architecture,
Security, Python, Tester and DevOps GO, plus DevOps S3/S3D. On designated SSH
PC WSL with Python 3.14, focused unittest passed 16 tests and direct Ruff
passed. Full `python3 tools/quality_gate.py quality` passed exit 0: 3,316
tests run, 37 skipped, 207.977 seconds. `git diff --check` passed. The
implementer did not run tests locally or execute native host operations.

Earlier Architecture review found that catalog selection validation needed
global unknown-dependency and cycle rejection, including unselected services.
The implementation now reuses the domain catalog validation path and includes
self-cycle, multi-service cycle and unknown-dependency regression tests.
Python 3.14 warned about two test regex escape sequences; raw strings fixed
these. An earlier full quality run failed mypy on the resolved selection type
and a test cases variable; explicit type narrowing and annotation fixed them.
The final exact-source gate passed after those corrections.

Source SHA-256:
`f99c93ea7be2734eacc410c513443be02aaba6fc4d8b3ff04292a994d79f6640`.
Test SHA-256:
`61e0112e6f10eaf5dd528468d95103a1322d9ed675fb8d27e73656813e1df9bd`.
Contract SHA-256:
`d13b093914e258436a829447f3305f16c055399a9660c16ea734beb780f6bf8f`.

## CP_RECORD

- sliceId: S449-MANIFEST-G2A
- workflowVersion: 1.51
- sliceTitle: Immutable schema-1 migration preview
- responsibleRole: Senior Python Automation Developer; root integration owner
- changedFiles: src/tiny_swarm_world/domain/lifecycle/manifest_v2.py,
  tests/domain/lifecycle/test_manifest_v2.py,
  .codex/evidence/slice-449-manifest-g2a-distribution.md,
  .codex/evidence/slice-449-manifest-g2a-consolidation.md
- qualityCommands: PYTHONPATH=src python3 -m unittest
  tests.domain.lifecycle.test_manifest_v2 tests.domain.lifecycle.test_models;
  python3 -m ruff check on new source and test;
  python3 tools/quality_gate.py quality; git diff --check
- qualityResult: PASS on designated SSH PC WSL Python 3.14: 16 targeted tests,
  direct Ruff and full quality exit 0, 3,316 tests run, 37 skipped, 207.977 s
- rollbackReference: 4beca580bb667279549874638716eee7c049fa1d
- arc42Updated: false
- adrUpdated: false
- commitSha: pending checkpoint commit
- limitations: preview only; no runtime schema-2 acceptance, persistence,
  adoption, capability guard, host admission, support qualification or live
  host operation. Host identities remain UNKNOWN and unadopted.
