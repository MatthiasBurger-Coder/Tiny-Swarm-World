# S449-ROUTE-POLICY-P0 consolidation

Status: IMPLEMENTED AND LOCALLY VERIFIED; CHECKPOINT PENDING. The domain
candidate is an ideal code-bound reference only, never actual runtime source,
host ownership, capability support, admission, persistence or live evidence.

It strictly revalidates v1/catalog input through G2a, restricts preset,
selection and explicit exposure/listen values, returns AUTHORITY_GAP for
affected 8086 selections and selected internal Swagger, compares complete
reviewed port/label tuples to the pure setup manifest, and derives the
domain-separated profile name from v1 UUID bytes while preserving original
UUID text. Route values are immutable planned policy, not observed host
settings; runtime_source remains UNKNOWN. Caller-supplied authority or source
claims are rejected. Differential, drift, collision and UUID vector tests are
present but have not been executed by this implementation stream.

Preflight base `e2e660521c46b672d456dd2b603a2da602ce8759`, six role design
GOs and serial S3/S3D are recorded in distribution. The integration owner reports final independent Security, Architecture and
Tester review GO, and exact-source designated SSH PC WSL targeted tests,
direct Ruff and full quality PASS. No local test or host operation was run by
the implementation stream.

## Verification and earlier review corrections

On designated SSH PC WSL with Python 3.14, exact-source targeted tests passed
39 tests, direct Ruff passed, and `python3 tools/quality_gate.py quality`
passed with exit 0: 3,377 tests run, 37 skipped, 205.881 seconds.
`git diff --check` passed. Python 3.12 and live host execution were not tested.

Earlier Security review found that a flattened port/label comparison lost
parent-service identity. The final candidate compares complete service,
port and label tuples and rejects unknown or duplicate groups; a regression
moves an unchanged port/label to another parent. Tester review identified that
caller catalog dependency semantics required code-bound validation. The final
candidate compares service identity, kind, mandatory state, dependencies and
presets against a reviewed immutable Classic snapshot; tests cover forged
Jenkins dependencies and other fields, independently declared fixture values
and actual native catalog loaded from isolated copied assets. Drift tests now
use real SetupManifest groups, and affected 8086 tests first validate complete
dependency closure. Independent Security, Architecture and Tester GO on the
final source/test hashes is reported in distribution.

## CP_RECORD

- sliceId: S449-ROUTE-POLICY-P0
- workflowVersion: 1.60
- sliceTitle: Code-bound scoped route policy and profile identity
- responsibleRole: Senior Python Automation Developer; root integration owner
- changedFiles: src/tiny_swarm_world/domain/lifecycle/scoped_route_policy.py,
  tests/domain/lifecycle/test_scoped_route_policy.py,
  .codex/evidence/slice-449-scoped-route-p0-distribution.md,
  .codex/evidence/slice-449-scoped-route-p0-consolidation.md
- qualityCommands: PYTHONPATH=src python3 -m unittest
  tests.domain.lifecycle.test_scoped_route_policy
  tests.domain.lifecycle.test_legacy_route_candidate
  tests.domain.lifecycle.test_manifest_v2 tests.domain.lifecycle.test_models;
  direct Ruff on new source and test; python3 tools/quality_gate.py quality;
  git diff --check
- qualityResult: PASS on designated SSH PC WSL Python 3.14; 39 targeted tests,
  Ruff, full quality exit 0, 3,377 tests run, 37 skipped, 205.881 seconds
- rollbackReference: e2e660521c46b672d456dd2b603a2da602ce8759
- arc42Updated: false
- adrUpdated: false
- commitSha: pending checkpoint commit
- limitations: Python 3.12 and live host execution not tested; code reference
  does not verify effective runtime source, ownership, host safety,
  capability support or admission. G2c and live host gates remain separate.
