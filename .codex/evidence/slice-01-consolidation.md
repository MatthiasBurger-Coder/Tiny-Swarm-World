# Slice 01 Consolidation

- Workflow: `workflow-issue-218-fr01-host-detection-20260712`
- Slice: `01` — Dedicated host detection boundary
- Integration owner: Codex / Tiny Swarm World lead architect
- Execution mode: sequential in the declared isolated worktree
- Live infrastructure: `NOT_RUN`
- Current decision: locally verified and ready for independent completion audit;
  PR/CI/Sonar/merge remain external release gates

## Consolidated implementation

The slice adds one typed host-classification contract, a pure domain classifier,
an application detector port/use case, focused Linux and WSL readers, concrete
composition, consolidated legacy consumers, an early read-only CLI, complete
FR-1 tests, and synchronized ADR/arc42/usage documentation. It implements no
FR-2 through FR-15 behavior.

## Accepted specialist findings

- Console/status UI: move `host detect` before application logger construction;
  qualify JSON with `live_readiness_verified=false`; state the limitation in
  human output; render native Windows interop as not applicable.
- Tester/DevOps: also dispatch before executable-PATH normalization; strengthen
  no-mutation sentinels for logger, directory/file writes, sync processes, async
  processes, and async shells; complete the issue evidence and red checkpoint.
- System Architect: reject `SANDBOX_UNVERIFIED` and unsupported Windows in
  `OsTypes.detect_current`; keep the explicit legacy string parser only; add
  the public readiness qualifier to arc42 Runtime View and Usage.
- Requirement Engineer: keep all 141 Issue #218 IDs in the issue matrix and
  retain strict FR-1 through FR-15 serialization; add explicit `OUT-001` and
  `QG-001` rows; preserve all four required Phase-3 inventories with later
  findings still `OPEN`/`IN_PROGRESS`.

All product/test corrections were implemented before the final focused and
full gates. Later matrix, inventory, and evidence-redaction corrections changed
no product behavior and passed `git diff --check`.

## Deferred or rejected findings

- A terminal dashboard was rejected as not applicable to one immediate result;
  line-oriented human output and deterministic JSON are the governed surfaces.
- Parallel write streams were rejected because the ADR, report, composition,
  CLI, compatibility consumers, and tests share one evolving contract.
- The review note that independent Incus/forwarding network-repair paths need a
  complete host gate is recorded for FR-7. It is not an FR-1 blocker and is not
  presented as implemented network preparation.
- Live WSL/Incus/Docker/Windows validation was not run because FR-1 is a
  read-only classification slice and the user did not authorize live mutation.

## Verification consolidation

- Regression-first red: 3 initial import errors; expanded 288-test checkpoint
  with 5 failures and 28 errors.
- Final focused suite: `PASS`, 321 tests.
- CI-marker simulation (`CI=1`): `PASS`, 321 tests after isolating the
  non-Linux fixture environment.
- Ruff: `PASS`.
- Import Linter: `PASS`, 3 contracts, 298 files/683 dependencies.
- Hexagonal architecture tests: `PASS`, 18 tests.
- Mypy: `PASS`, 486 source files.
- Full unittest discovery: `PASS`, 1,454 tests, 28 skips.
- Final full `quality` gate: `PASS`, 131.0 seconds; 1,454 tests in 97.968
  seconds with 28 expected skips.
- `git diff --check`: `PASS`.
- Actual WSL2 human/JSON classification: `PASS`, read-only; application log
  timestamp and size unchanged.
- Console/status UI independent review: `PASS`.
- System Architect independent review: `PASS`.

## Documentation consolidation

The accepted dedicated WSL2 host-boundary ADR and affected constraints,
building-block, runtime, deployment, quality, ADR-index, setup-safety, and user
usage documents describe only verified FR-1 behavior. Public readiness remains
explicitly unverified until later gates.

## Integration decision

The implementation is coherent, in scope, fail-closed, and locally green. It
passed final requirement/test evidence re-review and the independent Issue
Completion Auditor returned `PASS_FOR_PUBLICATION_PENDING_RELEASE`. The slice
must not be marked `DONE` until the single
implementation commit, PR checks including Python 3.12/Sonar, merge, cleanup,
and green merged-main verification complete.
