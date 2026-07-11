# Slice 01 Distribution Decision

Workflow ID: `workflow-issue-157-final-gaps-20260711`

Workflow version: `workflow-issue-157-final-gaps-v1.0.0`

Slice ID: `01`

Title: `Effective Model Seam And Positive Optional Routes`

## S3D Decision

- Result: `EXECUTION_PLAN` after the issue requirement matrix and this distribution record exist.
- Dependency position: first topological group `G1`; no predecessor.
- Execution mode: `sequential`.
- Selected streams: `backend`, `tests`, `architecture`.
- Affected but review-only concern: `security` (credential projection must remain value-free; no new persistence in this slice).
- Real subagents used: `yes`.
- Role-based fallback used: `no`.
- Git worktrees used: `no` for Slice 01; the verified main workflow worktree is required.

## Subagent Reviews

- `/root/s3d_preflight_review`: dependency graph, metadata, owners, quality gates and locks; no lock conflict.
- `/root/slice01_arch_review`: public model seam, domain skip semantics and shared-upstream label architecture; decision `READY_WITH_ACTIONS`.
- `/root/slice01_test_review`: requirement and regression coverage for `OPT-001..OPT-009`, `ARC-001..ARC-003`, `TST-002` and preserved baseline; no external blocker.

The write-capable owner is the Senior Python Automation Developer after these
reviews. Root Codex remains consolidation, test, commit and push owner.

## Expected Touched Files

- `src/tiny_swarm_world/domain/ingress/desired_state.py`
- `src/tiny_swarm_world/application/ports/repositories/port_effective_access_model_repository.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py`
- `tests/domain/ingress/test_desired_state.py`
- `tests/integration/test_optional_service_routing.py`
- `tests/support/effective_access_model_fixture.py`
- `.codex/evidence/workflow-issue-157-final-gaps-20260711/slice-01-distribution.md`
- `.codex/evidence/workflow-issue-157-final-gaps-20260711/slice-01-consolidation.md`

No committed `infra/config/services.yml`, `infra/config/ports.yaml` or compose
configuration may be changed by this slice.

## Locks

File locks are exactly the expected product/test files above. Contract locks:

- one effective access model feeds all consumers;
- enabled conditional routes are not simultaneously skipped;
- App and API coexist on the `tiny-swarm` upstream without label loss.

Architecture locks:

- domain stays infrastructure- and I/O-free;
- YAML parsing stays in infrastructure;
- product code does not depend on test support.

## Conflict Risks

- The public model seam and renderer are a shared foundation for all three G2 slices.
- App/API require two explicit router-to-Traefik-service bindings because they share one Swarm service but use different internal ports.
- Tests must load only temporary structured YAML and synthetic compose files.
- Broad line-ending-only changes are forbidden.
- The ignored local env file is not an input and must not be read.

These concerns overlap inside the same small model/renderer seam, so separate
write-capable backend and test streams would increase ownership conflicts.
Sequential execution was therefore selected despite real subagent reviews.

## Quality Gates

Targeted first:

```bash
PYTHONPATH=src python3 -m unittest tests.domain.ingress.test_desired_state
PYTHONPATH=src python3 -m unittest tests.integration.test_optional_service_routing
PYTHONPATH=src python3 -m unittest tests.integration.test_service_access_routing
```

Required before the Slice 01 checkpoint:

```bash
python3 tools/quality_gate.py arch-tests
python3 tools/quality_gate.py quality
git diff --check
git diff --cached --check
```

No live infrastructure command is permitted.

## Consolidation Plan

1. Implement the minimal public port, skip correction and grouped label rendering.
2. Add isolated fixture support and regression-first positive/negative tests.
3. Inspect every touched file and line-ending behavior.
4. Run targeted tests, architecture tests and the full local quality gate.
5. Record accepted/rejected findings and results in `slice-01-consolidation.md`.
6. Stage only Slice 01 files, create exactly one Slice 01 checkpoint commit and push only the workflow branch.

Parallelization is rejected for Slice 01 because product and test changes share
one unstable foundational contract and must be stabilized before G2 worktrees
are created.
