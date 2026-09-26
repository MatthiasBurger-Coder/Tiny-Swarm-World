# ARCH-03.12 — Explicit operation results and failure model

Status: PLANNED; no product implementation in this authoring change.
Issue: [#355](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/355).
Parent: [#313](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/313).

## Verified baseline

Platform results live in `application/services/platform/workflow/results.py`;
artifacts and deployment each define their own results in `workflows.py`, and
setup in `setup/workflow.py`. Platform runtime and setup catch broad exceptions.
`AsyncPortCommandRunner` raises infrastructure-owned `CommandExecutionError`.
`LxcNodeCommandResult` does not preserve the async runner failure hint.
Update observation already has a port-owned error, while update state storage can
leak filesystem/value exceptions. Existing update recovery verifies convergence.
CLI success is tied to `completed`; verified recovery already returns that status.

## Planned ownership

Use a shared immutable application-port result/failure contract. Infrastructure
adapters classify technology failures; workflows aggregate expected outcomes;
CLI/reporting renders safe context and retains compatibility. Domain stays pure,
composition stays at the edge, and lifecycle dispatch remains thin.

See [proposed ADR](../09_decisions/adr-explicit-operation-results.adoc) for semantic
invariants, compatibility and alternatives. S355-01 must accept that decision and
the complete lifecycle inventory before product implementation.

## Migration and evidence

[Active workflow](../../workflow/workflow.md) sequences inventory, integrated
contract, adapters, platform/recovery, cross-family aggregation, CLI and final
audit. All requirement evidence is initially OPEN. Issue execution evidence belongs
in `.tiny-swarm/evidence/issue-355/`. Existing #353/#354 boundaries are prerequisites;
#356 retry/rollback/idempotency behavior is outside scope.

Arc42 check: layer contracts, lifecycle orchestrator, process execution, Classic
update and installer reporting decisions reviewed. This proposed ADR does not
supersede them. Update implemented building-block/runtime/concept descriptions
only after execution evidence. No live or external verification is claimed.
