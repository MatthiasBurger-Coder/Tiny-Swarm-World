# S449-ROUTE-POLICY-P0A consolidation

Status: IMPLEMENTED AND LOCALLY VERIFIED; CHECKPOINT PENDING. This candidate is an
explicitly unverified pure rendering of legacy setup code, not an authoritative
scoped route policy, v2 conversion, host qualification or live admission.

The candidate requires an explicit stock-context assertion, published exposure,
validated v1 manifest/catalog, canonical typed listener and gateway; it keeps
all legacy port requirements, including compatibility ports. Unsupported input,
unknown names, duplicate listeners and malformed requirements produce the fixed
AUTHORITY_GAP result. Output is immutable and preserves v1 UUID text; actual host,
profile, ownership, NAT and proxy-protocol are UNKNOWN. Source applicability
is a caller statement, not an independently verified observation.

Preflight base `a0fc99c87b16ab890a61ea9b2218a06aa089b4ae` and six same-tuple
role GOs are recorded in P0a distribution. The integration owner reports six role GO decisions rebound to the final
candidate, plus exact-source SSH PC WSL targeted tests, Ruff and full quality
PASS. No local tests or host operations were executed by this worker.

## Verification and earlier failure

The final exact-source designated SSH PC WSL Python 3.14 run passed 26
targeted tests and direct Ruff. Full `python3 tools/quality_gate.py quality`
passed exit 0: 3,363 tests run, 37 skipped, 207.212 seconds.
`git diff --check` passed. Python 3.12 and live host execution were not tested.

An earlier full quality run failed mypy because one test reused a loop
variable across incompatible input categories. Distinct variables corrected
the annotation issue without changing the tested cases; the full gate passed
on the corrected test bytes. Source and test hashes and six role rebind
decisions are recorded in distribution.

## CP_RECORD

- sliceId: S449-ROUTE-POLICY-P0A
- workflowVersion: 1.58
- sliceTitle: Legacy published route candidate
- responsibleRole: Senior Python Automation Developer; root integration owner
- changedFiles: src/tiny_swarm_world/domain/lifecycle/legacy_route_candidate.py,
  tests/domain/lifecycle/test_legacy_route_candidate.py,
  .codex/evidence/slice-449-route-p0a-distribution.md,
  .codex/evidence/slice-449-route-p0a-consolidation.md
- qualityCommands: PYTHONPATH=src python3 -m unittest
  tests.domain.lifecycle.test_legacy_route_candidate
  tests.domain.lifecycle.test_manifest_v2
  tests.application.services.platform.test_lxc_service_exposure;
  direct Ruff on new source and test; python3 tools/quality_gate.py quality;
  git diff --check
- qualityResult: PASS on designated SSH PC WSL Python 3.14; 26 targeted tests,
  Ruff, full quality exit 0, 3,363 tests run, 37 skipped, 207.212 seconds
- rollbackReference: a0fc99c87b16ab890a61ea9b2218a06aa089b4ae
- arc42Updated: false
- adrUpdated: false
- commitSha: pending checkpoint commit
- limitations: Python 3.12 and live host execution not tested; this unverified
  candidate establishes neither authoritative scoped route policy nor host
  safety, capability support, v2 conversion or live admission.
