# Slice 03 Distribution Decision

Workflow: `issue-183-20260808`
Slice: `03` — Extract the Swarm stack runtime, assets, and prerequisite strategies

## Affected areas

* `LxcSwarmRuntime` stack deployment, service status, secrets, migration-lock,
  port reconciliation, dashboard, prerequisite, and asset-transfer behavior;
* new `lxc/swarm/` infrastructure package;
* focused Swarm runtime, asset, and prerequisite tests.

## Execution decision

* Chosen mode: `sequential`.
* Real Codex subagents used: `No callable subagent surface is available.`
* Fallback role-based review used: `Yes`.
* Git worktrees used: `No`; the legacy runtime and shared compatibility tests
  are locked for this slice.
* Selected streams: backend extraction, tests, architecture, and runtime
  safety review.
* Documentation stream: review-only; no Arc42 change is required until the
  extracted responsibilities are verified at consolidation.

## Fallback role review

* Senior Python Automation Developer: extract Swarm behavior into focused
  infrastructure collaborators while retaining legacy exports and delegation.
* Senior System Architect: preserve `PortSwarmStackRuntime`, keep strategy
  registration infrastructure-owned, and avoid application-service changes.
* Senior Tester: preserve stack ordering, asset contents, port reconciliation,
  secret handling, service status, dashboard, and migration-lock seams without
  live commands.
* Senior DevOps Engineer: inspect deployment and prerequisite command safety;
  no Incus, Docker, Swarm, registry, or credential-backed command is allowed.

## Expected touched files/directories

* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/swarm/`
* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py`
* `tests/infrastructure/adapters/clients/lxc/swarm/`
* `.codex/evidence/slice-03-distribution.md`
* `.codex/evidence/slice-03-consolidation.md`

## Conflict risks

The legacy runtime contains multiple responsibilities and its tests patch
private methods directly. Extraction must preserve those methods as stable
compatibility seams while moving implementation behind collaborators. Asset
transfer and prerequisite ordering share the shell gateway and must remain
serial. No stream may change application ports or introduce live execution.

## Quality gates

* focused Swarm runtime, asset, and prerequisite unittest suite;
* `python3 tools/quality_gate.py lint`;
* `python3 tools/quality_gate.py typecheck`;
* `python3 tools/quality_gate.py arch-lint`;
* `python3 tools/quality_gate.py arch-tests`;
* `git diff --check`.

## Consolidation plan

Codex will inspect extracted ownership and compatibility exports, run focused
and architecture checks, record findings, and create one Slice 03 checkpoint
commit before Slice 04.

## Parallelization decision

Rejected because stack deployment, prerequisite ordering, asset transfer, and
the legacy compatibility module share files, collaborators, and behavior
contracts.
