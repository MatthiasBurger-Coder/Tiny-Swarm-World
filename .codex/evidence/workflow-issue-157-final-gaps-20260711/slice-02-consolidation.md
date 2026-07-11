# Slice 02 Consolidation

Workflow ID: `workflow-issue-157-final-gaps-20260711`

Workflow version: `workflow-issue-157-final-gaps-v1.0.0`

Slice ID: `02`

Title: `Productive Redacted Routing Evidence`

Stream branch: `fix/issue-157-final-gaps-20260711-slice-02-backend`

Responsible role: Senior Python Automation Developer

Consolidation owner: Root Codex / Tiny Swarm World Lead Architect

## Read-Only Four-Role Gate

Decision: `READY_WITH_ACTIONS`; no workflow stop condition was found.

- Requirement Lead: the issue matrix exists before implementation and retains
  `EVD-001..EVD-010`, `TST-001` and the Slice 02 contributions to
  `ARC-001..ARC-004`. Other IDs remained read-only constraints.
- System Architect: Slice 01 commit
  `578f5e57d28cc5c6536781d88e88bd6cc7b69cea` provides the stable
  `PortEffectiveAccessModelRepository` seam. The existing deployment
  `pre_apply_steps` contract supports fail-closed evidence generation without
  changing setup phase order.
- Test Lead: application projection, local atomic persistence and composition
  ordering are independently testable with fakes, mocks and temporary
  directories. No browser, DNS, Docker, Traefik or Incus dependency is needed.
- Security / Evidence Reviewer: a typed allowlisted document can omit route
  notes and retain only credential `username_label` and `item_reference`.
  Neither environment credential discovery nor arbitrary mapping or exception
  serialization is needed.

## Accepted Implementation

- Added a dedicated routing-evidence repository port with typed, explicitly
  serialized evidence records. The adapter accepts only the typed effective
  access document, not an arbitrary mapping.
- Added `WriteEffectiveAccessModelEvidence`, which obtains the central model
  through `PortEffectiveAccessModelRepository`, injects a timezone-aware UTC
  clock, deterministically sorts all repeated collections and writes one fixed
  allowlisted projection.
- The top-level contract contains exactly the required fields:
  `evidence_kind`, `generated_at`, `service_profile`, `public_ports`,
  `gateway_public_ingress_ports`, `diagnostic_fallback_ports`,
  `service_access_preferred_url_source`, `routes`, `health_check_targets`,
  `service_access_links`, `skipped_routes` and `result`.
- Credential projections contain only `username_label` and `item_reference`.
  Credential notes, no-login notes, process-environment values and arbitrary
  model mappings are not inputs to serialization. Routed URLs fail closed when
  they contain credentials, a query, fragment, explicit port, a non-HTTPS
  scheme or a mismatched host.
- Added the local adapter target
  `.tiny-swarm-world/evidence/solid-typed-evidence/routing/effective-access-model.json`.
  It creates parents, writes a same-directory temporary file, flushes and
  fsyncs it, applies owner-only modes where supported, and atomically replaces
  the target. A failed replacement preserves the prior target and removes the
  temporary file.
- Composition now passes the selected service profile to both
  `ComposeFileRepositoryYaml` and the evidence use case. The evidence writer
  is the first deployment pre-apply step, before asset preparation and before
  any stack apply. Its failure returns `failed_to_prepare` and prevents the
  first stack step from running.
- No constructor performs evidence I/O, no global singleton was added, and no
  setup workflow phase was added, removed or reordered.

## Files Changed By Stream

Product code:

- `src/tiny_swarm_world/application/ports/repositories/port_routing_evidence_repository.py`
- `src/tiny_swarm_world/application/services/deployment/write_effective_access_model_evidence.py`
- `src/tiny_swarm_world/application/services/deployment/__init__.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/routing_evidence_local_repository.py`
- `src/tiny_swarm_world/infrastructure/composition.py`

Tests:

- `tests/application/services/deployment/test_write_effective_access_model_evidence.py`
- `tests/infrastructure/adapters/repositories/test_routing_evidence_local_repository.py`
- `tests/infrastructure/test_composition.py`

Workflow evidence:

- `.codex/evidence/workflow-issue-157-final-gaps-20260711/slice-02-distribution.md`
- `.codex/evidence/workflow-issue-157-final-gaps-20260711/slice-02-consolidation.md`

No nonlocked file was changed.

## Requirement Verification

- `EVD-001..EVD-004`: typed application use case, exact output contract,
  injected UTC timestamp, selected profile and `result: generated` are covered
  by the application-service tests.
- `EVD-005..EVD-006`: secret-note, private-key-marker and environment sentinel
  values are absent; credential shapes have exactly two allowed fields;
  credential-bearing URLs fail closed before persistence.
- `EVD-007`: permuted route, fallback and skipped input produces an identical
  document; routes, health targets, links, fallbacks and skips have stable sort
  keys, while JSON keys use `sort_keys=True`.
- `EVD-008`: parent creation, same-directory replacement, private target mode,
  prior-target preservation and temporary cleanup are covered by adapter tests.
- `EVD-009`: composition tests verify first-pre-apply placement, selected
  profile reuse and failure before any stack apply.
- `EVD-010`: adapter path remains under `.tiny-swarm-world`, and the repository
  ignore rule `/.tiny-swarm-world/` is asserted.
- `ARC-001..ARC-003`: application depends only on domain values and ports;
  filesystem/JSON concerns remain in infrastructure; the compose repository is
  the single model provider. Import-linter and architecture tests pass.
- `ARC-004`: setup phase order and all provider, direct-port, DNS, TLS,
  messaging and Infisical behaviors are unchanged by this slice.
- `TST-001`: productive writer, redaction, deterministic sorting, atomicity and
  runtime integration all have static automated coverage.

## Tests And Quality

Targeted tests after the final implementation:

```text
PYTHONPATH=src python3 -m unittest tests.application.services.deployment.test_write_effective_access_model_evidence
PASS - 3 tests

PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_routing_evidence_local_repository
PASS - 3 tests

PYTHONPATH=src python3 -m unittest tests.infrastructure.test_composition
PASS - 87 tests
```

Additional gates:

```text
python3 tools/quality_gate.py lint
PASS - Ruff all checks passed

python3 tools/quality_gate.py typecheck
PASS - Mypy found no issues in 471 source files

python3 tools/quality_gate.py arch-lint
PASS - 3 contracts kept, 0 broken; 290 files and 657 dependencies analyzed

python3 tools/quality_gate.py arch-tests
PASS - 18 tests

python3 tools/quality_gate.py quality
PASS
- Ruff: pass
- Import Linter: 3 contracts kept, 0 broken
- Architecture tests: 18 passed
- Mypy: no issues in 471 source files
- Unittest: 1,354 tests run; 1,326 passed and 28 skipped
```

All commands ran through WSL with the established project virtual-environment
toolchain. No live infrastructure command ran.

## Conflicts And Fixes

- File, contract and architecture lock conflicts: none.
- Merge conflicts: none; this worker did not merge.
- Initial targeted adapter test: classified `TEST_FAILURE`. A temporary
  `ProjectPaths` root correctly failed the existing verified-repository guard;
  the isolated adapter test was corrected to use the adapter's explicit test
  root seam. Product path validation was not weakened.
- Initial Mypy result: classified `BUILD_FAILURE`. Three fixed-length tuple
  inferences in the new test and one heterogeneous pre-apply list annotation
  were corrected with explicit bounded types. No assertion or architecture
  rule was removed.
- Final retry results: all targeted and required gates pass.

## Security And Evidence Review

- Raw `.env` content and the referenced `live-installation.env` were not read.
- No password, token, secret value, private key, authorization header, raw
  exception payload or environment mapping is serialized.
- Expected exception handling records only the sanitized failure class through
  the existing deployment workflow; the evidence adapter does not serialize
  exceptions.
- Product routing evidence remains generated model evidence only. It does not
  claim live reachability, readiness or login success.
- Live Selenium was not run and no live-pass claim is made.

## Documentation And ADR Status

- arc42 or user documentation changed in this slice: `false`.
- Reason: Slice 05 owns documentation synchronization after all G2 product and
  test streams are consolidated and verified.
- ADR changed: `false`.
- Review decision: the existing Traefik ingress, setup-safety and explicit
  live-consent decisions cover this bounded implementation; no new decision is
  introduced.

## Final Integration Decision

Decision: `READY_FOR_ROOT_CONSOLIDATION`.

Slice 02 implementation and verification are complete within its locks. The
worker did not commit, push, merge, run live infrastructure or claim final
Issue #157 completion. Root Codex remains responsible for diff review,
consolidation into the workflow branch, checkpoint publication and downstream
Slices 05/06.
