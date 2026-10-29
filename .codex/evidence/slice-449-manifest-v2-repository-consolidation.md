# S449-MANIFEST-V2-REPOSITORY consolidation

Status: IMPLEMENTED AND LOCALLY VERIFIED; CHECKPOINT PENDING.

The candidate introduces an immutable, redacted UNADOPTED draft recomputed
from G2c/P0, a separate closed redacted versioned repository port, and a fixed
operator-local staging adapter. V1 decoding and all existing runtime,
canonical-manifest, CLI and host paths remain unchanged. This is not a
canonical admitted V2, host qualification, capability support or migration.

The adapter uses bounded duplicate-rejecting JSON, descriptor-relative
no-follow path traversal, owner/mode/link checks, a stable cooperative lock
inode and SHA-256 byte tokens. Same-byte no-op and byte-identical ABA are
documented separately from stale conflicts; post-possible-replace failure
returns UNCERTAIN. These are staging contracts under the documented cooperative
writer assumptions, not claims of hostile privileged-writer resistance.

Original preflight and the later approved complexity-remediation S3/S3D
handoff are recorded in distribution. Final SSH PC WSL verification and
independent role status are recorded below. No local test or host operation
was run by the implementation stream.

## Verification and prior findings

The integration owner reports Security, Architecture, Tester, Requirement,
Python and DevOps GO for the final facade, JSON, filesystem and adapter-test
hashes listed in distribution; DevOps also reviewed task scope. These reports
do not assert an independent GO on the complete seven-file tuple.

On designated SSH PC WSL Python 3.14, the exact candidate transferred in a tar
with SHA-256 prefix `071ec104` passed 48 targeted tests and direct Ruff.
`python3 tools/quality_gate.py quality` passed exit 0: 3,436 tests run,
37 skipped, 205.904 seconds. `git diff --check` passed. Python 3.12 and live
host execution were not tested.

An earlier full gate failed four complexity findings for the combined adapter,
class, CAS function and JSON parser. Under separately reviewed locks the
candidate was split into a facade, bounded JSON parser and filesystem/CAS
operations; no thresholds, baseline or exception list were changed. The full
gate passed after the split.

Earlier Security reviews identified unsynchronized created/existing parent
directory entries and an unsafe same-byte no-op after an uncertain replace.
The final filesystem path synchronizes each parent on write and requires file
and staging-directory synchronization before no-op success. Tests also exercise
lock-inode changes, pre/post replace failures, controlled child-process crashes
and read-only reconciliation. Byte-identical ABA remains undetectable; no
stronger claim follows from these tests.

## CP_RECORD

- sliceId: S449-MANIFEST-V2-REPOSITORY
- workflowVersion: 1.67
- sliceTitle: Isolated unadopted versioned manifest repository
- responsibleRole: Senior Python Automation Developer; root integration owner
- changedFiles: src/tiny_swarm_world/domain/lifecycle/manifest_v2_record.py,
  src/tiny_swarm_world/application/ports/lifecycle/versioned_manifest.py,
  src/tiny_swarm_world/infrastructure/adapters/lifecycle/versioned_manifest_repository.py,
  src/tiny_swarm_world/infrastructure/adapters/lifecycle/versioned_manifest_json.py,
  src/tiny_swarm_world/infrastructure/adapters/lifecycle/versioned_manifest_fs.py,
  tests/domain/lifecycle/test_manifest_v2_record.py,
  tests/infrastructure/adapters/lifecycle/test_versioned_manifest_repository.py,
  .codex/evidence/slice-449-manifest-v2-repository-distribution.md,
  .codex/evidence/slice-449-manifest-v2-repository-consolidation.md
- qualityCommands: PYTHONPATH=src python3 -m unittest
  tests.domain.lifecycle.test_manifest_v2_record
  tests.infrastructure.adapters.lifecycle.test_versioned_manifest_repository
  tests.infrastructure.adapters.lifecycle.test_manifest
  tests.test_migration_preview_cli; direct Ruff on new source/tests;
  python3 tools/quality_gate.py quality; git diff --check
- qualityResult: PASS on designated SSH PC WSL Python 3.14; 48 targeted tests,
  Ruff, full quality exit 0, 3,436 tests run, 37 skipped, 205.904 seconds
- rollbackReference: 9626d804d3272bae6208eecf9ecc97c3a196ef22
- arc42Updated: false
- adrUpdated: false
- commitSha: pending checkpoint commit
- limitations: Python 3.12 and live host execution untested; final reported
  role reviews bind four specified hashes, not all seven files. No canonical
  persistence, runtime integration, admitted ownership, host safety,
  capability support or live qualification.
