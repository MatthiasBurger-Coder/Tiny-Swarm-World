# Issue #184 — S184-02 Consolidation

## Stream results

- Backend/Python: PASS. Command transport/result types moved to
  `lxc/command/node_command.py`; deterministic command construction moved to
  `lxc/command/args.py`; node state/safety, profile policy and resource
  resolution now have dedicated modules.
- Architecture: PASS. `LxcNodeProvider` remains the lifecycle facade, all
  extracted modules stay under infrastructure, and the #189 backend resolver
  remains the sole mapping source.
- Tests/quality: PASS. Existing lifecycle behavior and new module seams are
  covered by focused tests; legacy imports remain stable.
- Security: PASS. Bounded subprocess timeout and safe text handling are
  preserved; profile/device safety checks remain enforced.
- Documentation: deferred to S184-03 for after-inventory and Arc42 status.
- Real subagents: unavailable; role-based fallback review was used.

## Accepted findings

- `LxcNodeCommandResult`, `LxcNodeCommandRunner` and
  `AsyncLxcNodeCommandRunner` are owned by the command boundary and re-exported
  through the legacy module.
- `ObservedNode`, `NodeLookup` and `TeardownNodePlan` are owned by the node
  boundary; legacy private aliases preserve current tests and compatibility.
- Profile safety/reconciliation policy is isolated from command construction.
- Resource parsing, validation and backend resource evidence are isolated from
  node lifecycle orchestration.
- No duplicate backend mapping was introduced.

## Rejected or deferred findings

- Full typed evidence-builder redesign is deferred to #191.
- Public application-port changes are out of scope.
- Live LXC validation was not authorized and was not run.

## Conflicts

- No file, contract or architecture lock conflict was found.
- No merge conflict occurred; the mandatory serial execution mode was retained.

## Verification

- Targeted Ruff: PASS.
- Focused LXC, command, node, profile, resource and architecture tests: 64 passed.
- Legacy lifecycle regression tests: PASS within the focused run.
- Full required `python3 tools/quality_gate.py quality`: scheduled after S184-03
  because the completion slice owns the final architecture/evidence audit.

## Final integration decision

Decision: `S184-02_READY_FOR_S184-03`.

The extracted boundaries are behavior-preserving and ready for the final
regression, duplicate/compatibility guard and completion audit.
