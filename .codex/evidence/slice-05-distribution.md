# Slice 05 Distribution Decision

Workflow: `issue-183-20260808`
Slice: `05` — Migrate composition and preserve the compatibility surface

## Affected areas

* `composition.py` and `composition_lxc_runtimes.py` concrete imports;
* the legacy `lxc_swarm_runtime.py` compatibility facade;
* composition, logging, adapter, and architecture-boundary tests.

## Execution decision

* Chosen mode: `sequential`.
* Real Codex subagents used: `No callable subagent surface is available.`
* Fallback role-based review used: `Yes`.
* Git worktrees used: `No`; composition and all infrastructure tests share
  import and patch locks.
* Selected streams: architecture/composition, Python compatibility, tests, and
  documentation-boundary review.
* Live/runtime stream: review-only; no infrastructure commands are allowed.

## Fallback role review

* Senior System Architect: make composition the concrete wiring root and keep
  the legacy module limited to compatibility facades/exports.
* Senior Python Automation Developer: migrate imports without changing
  constructor arguments, provider selection, or patch targets.
* Senior Tester: run composition, logging, runtime, and architecture tests;
  preserve legacy imports without broad test rewrites.
* Senior Documentation Engineer: verify the Arc42 building-block statement
  remains aligned with the extracted package ownership.

## Expected touched files/directories

* `src/tiny_swarm_world/infrastructure/composition.py`
* `src/tiny_swarm_world/infrastructure/composition_lxc_runtimes.py`
* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py`
* `tests/infrastructure/test_composition.py`
* `tests/infrastructure/test_lxc_runtime_logging.py`
* `tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py`
* `tests/architecture/test_lxc_runtime_boundaries.py`
* `.codex/evidence/slice-05-distribution.md`
* `.codex/evidence/slice-05-consolidation.md`

## Conflict risks

Composition has several provider-selected construction paths. Import migration
must preserve runtime constructor arguments and old patch paths. The legacy
module still contains renamed historical implementations from the extraction;
this slice must remove that dead duplicate implementation or prove it is not
reachable, while preserving public compatibility names.

## Quality gates

* targeted composition, logging, and LXC runtime unittest suite;
* `python3 tools/quality_gate.py arch-tests`;
* full `python3 tools/quality_gate.py quality`;
* `git diff --check`.

## Consolidation plan

Codex will migrate composition imports, remove unreachable legacy duplicate
classes/helpers where safe, add or strengthen the architecture guard, run the
targeted and full local gates, record findings, and create one Slice 05
checkpoint.

## Parallelization decision

Rejected because composition, the legacy module, and the infrastructure test
suite share import, constructor, and patch contracts.
