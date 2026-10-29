# S449-CAPABILITY-G1 consolidation

Status: IMPLEMENTED AND LOCALLY VERIFIED; CHECKPOINT PENDING. This is a domain-only
classification foundation. It does not integrate or prove any runtime guard,
host protection, live capability support or change to the legacy adapter.

The typed classifier accepts only actual local IntentKind members, recognizes
legacy only without a version, validates narrowly canonical ASCII versions,
and returns UNSUPPORTED for every canonical installation-scoped version. The
exposed support registry is an empty immutable frozenset; classification
never derives support from its contents.

Baseline and preflight: `eb7a57f7f4f9650892e268f27f32ab3c53c14500`;
`slice-449-capability-g1-distribution.md` records six independent plan GOs and
serial S3/S3D. Test implementation covers typed identity, invalid values,
boundary canonical versions, immutable support, no registration, no host I/O,
and explicit legacy semantics.

The integration owner reports a designated SSH PC WSL Python 3.14 focused
run of 7 tests PASS and direct Ruff PASS. The full quality gate on that
host passed with exit 0 on Python 3.14: 3,307 tests run, 37 skipped,
221.824 seconds. No native host operation was run.

An earlier focused run also passed 7 tests, but the full quality gate failed
typecheck because a test-local set needed an annotation. The set is now typed;
the corrected full gate passed. Before that, the Tester review identified that
a string subclass could spoof length. The candidate now accepts exactly the
built-in str type, with regression tests, and the contract was clarified.
The integration owner reports six source/contract GO decisions from
Requirement, Architecture, Security, Python, Tester and DevOps. DevOps
revalidated S3/S3D GO on the corrected contract and source/test hashes.
The implementer ran no local tests or host operations. Local quality cannot
establish host support.

Final candidate SHA-256:

- Contract: `88a54329249894c8698f0c425dd5d861423e53ca70aea2a129a7e1b442a3fee3`
- Source: `235e03236ab1d46fa058ed852d8a21db551621aaa49dd9e26f2c96e4125debf1`
- Tests: `092e288a4344dd5f5ecc4bd517498c4e351cc993530b85a7c0b5c1094f82b84b`

## CP_RECORD

- sliceId: S449-CAPABILITY-G1
- workflowVersion: 1.50
- sliceTitle: Domain-only typed Incus capability classification
- responsibleRole: Senior Python Automation Developer; root consolidation owner
- changedFiles: src/tiny_swarm_world/domain/lifecycle/incus_capability.py,
  tests/domain/lifecycle/test_incus_capability.py,
  .codex/evidence/slice-449-capability-g1-contract.md,
  .codex/evidence/slice-449-capability-g1-distribution.md,
  .codex/evidence/slice-449-capability-g1-consolidation.md
- qualityCommands: PYTHONPATH=src python3 -m unittest
  tests.domain.lifecycle.test_incus_capability; python3 -m ruff check on
  source and test; python3 tools/quality_gate.py quality; git diff --check
- qualityResult: PASS on designated SSH PC WSL Python 3.14: targeted 7 tests;
  Ruff; full quality exit 0, 3,307 tests, 37 skipped, 221.824 seconds
- rollbackReference: eb7a57f7f4f9650892e268f27f32ab3c53c14500
- arc42Updated: false
- adrUpdated: false
- commitSha: pending checkpoint commit
- limitations: no runtime wiring, caller guard, live support, host admission,
  fixture qualification or legacy provider modification. Supported versions
  remain empty; every valid scoped version is UNSUPPORTED.
