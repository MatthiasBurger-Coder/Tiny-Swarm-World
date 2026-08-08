# Slice 01 Consolidation

- Workflow: `issue-232-20260808`
- Slice: `01` — Domain image-contract and inventory invariants
- Execution mode: serial fallback review; no callable subagents were available.
- Accepted streams: backend/domain, tests, architecture, security/evidence.
- Rejected streams: frontend and live/runtime; neither is in Slice 01 scope.

## Accepted Findings

- `ContainerImageContract` keeps its existing construction API and now exposes
  safe static validation for implicit `latest` and malformed digest references.
- Version tags remain supported and full sha256 digests render without adding a
  second separator.
- `ArtifactImageRequirement`, `ArtifactContractIssue` and
  `ArtifactImageInventory` remain parser- and adapter-independent domain values.
- Inventory validation covers missing/unused contracts, duplicate logical
  contexts, conflicting references and context/source mismatches.
- Domain import boundaries remain unchanged.

## Rejected Findings

- No live registry/Docker check was added to the domain slice; that belongs to
  Slice 05 and must cross application ports.
- No Compose/YAML or environment override resolution was added; that belongs to
  Slice 03 and remains an infrastructure/application concern.
- A duplicate image reference used by multiple deployment services is not
  rejected as an artifact contract conflict; one contract may be consumed by
  more than one service target.

## Files Changed

- `src/tiny_swarm_world/domain/artifacts/container_image_contract.py`
- `src/tiny_swarm_world/domain/artifacts/__init__.py`
- `tests/domain/artifacts/test_container_image_contract.py`
- `.codex/evidence/issue-232/slice-01-distribution.md`
- `.codex/evidence/issue-232/slice-01-consolidation.md`

Historical `.codex/evidence/slice-01-distribution.md` from Issue #218 was
verified unchanged and is not part of this slice.

## Conflicts

- Found: the legacy global Slice 01 distribution path was already owned by
  Issue #218.
- Resolved: Issue #232 evidence is namespaced under
  `.codex/evidence/issue-232/`; the active workflow and context pack were
  updated in a separate guarded workflow-governance commit before this slice.

## Tests and Quality

- `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World && PYTHONPATH=src python3 -m unittest tests.domain.artifacts.test_container_image_contract'` — PASS, 6 tests.
- `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World && python3 tools/quality_gate.py typecheck'` — PASS.
- `wsl bash -lc 'cd /mnt/d/Projects/Tiny-Swarm-World && python3 tools/quality_gate.py quality'` — PASS; verification-policy, lint, arch-lint, arch-tests and typecheck passed; full discovery passed with 1600 tests and 28 skipped.
- `git diff --check` — required before checkpoint staging.
- Live Docker/registry/Nexus validation — `LIVE_CONSENT_MISSING`; not run.
- External quality result — not inferred from local checks.

## Documentation Updates

- No product documentation change was required for this domain-only slice.
- Workflow evidence namespace and context-pack hash were synchronized before
  implementation to preserve historical evidence ownership.

## Final Integration Decision

`ACCEPTED_FOR_SLICE_CHECKPOINT`: domain invariants are implemented and
verified; later slices must connect the inventory to profile/Compose resolution,
ports, static preflight, live readiness and fail-closed orchestration.
