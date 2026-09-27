# ARCH-03.12 — Explicit operation results and failure model

Status: IMPLEMENTED and independently audited; S355-07 architecture and local quality passed.
Issue: [#355](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/355).
Parent: [#313](https://github.com/MatthiasBurger-Coder/Tiny-Swarm-World/issues/313).

## Implemented ownership

Source paths below are relative to `src/tiny_swarm_world/`.
`application/ports/operation_result.py` owns immutable `OperationFailure` and
`OperationResult`, the outcome/recoverability enums, and typed `OperationError`.
Domain remains independent of application. Infrastructure translates expected
technical failures at ports; compatibility bridges preserve existing exception
imports and catch hierarchies where required. ARCH-03.11 process runners retain
process ownership.

Platform results in `application/services/platform/workflow/results.py`, artifacts
and deployment results in their respective `workflows.py`, and setup results in
`application/services/setup/workflow.py` expose additive `operation_result` fields.
Older constructor calls can omit the field; serialization then returns `null`.
`application/services/shared/operation_results.py` aggregates explicit work evidence
and validates serialized failure origins against caller-owned allowlists.

## Outcomes and runtime behavior

The six outcomes are `success`, `failed`, `partial`, `rolled_back`, `blocked`,
and `refused`. Confirmed completed, pending and uncertain operations are disjoint
immutable tuples. Partial completion requires confirmed work and an incomplete
request; starting a command alone does not prove completion. Guards alone are not
completed requested work. Legacy blocked status after confirmed work can accompany
a common partial outcome. Timeout retains uncertain effects separately from pending
work, including setup's in-flight phase snapshot.

`application/services/platform/workflow/update.py` reports `rolled_back` only after
observing restoration to the recorded original image. Saved state or an attempted
rollback is insufficient. Original failure context is retained where available;
failed recovery retains available original failure context together with recovery
failures. A recovered child keeps
its resolved history in its nested result; setup does not promote that history to
an unresolved parent failure or claim that the entire setup was rolled back.

Failure fields identify operation, component, catalogue cause, recoverability and
recommended action. The enum supports `recoverable`, `nonrecoverable` and `unknown`;
the current cause catalogue uses only the latter two. Unknown effects do not promise
a safe retry. Actions are static operator guidance and are never executed by rendering.
Expected typed failures retain their origin. Existing broad compatibility catches
classify unexpected errors as `unexpected_failure`; previously propagating faults
remain distinguishable. Cancellation and process-control exceptions retain their
propagation or explicit entrypoint exit mapping.

See the [accepted ADR](../09_decisions/adr-explicit-operation-results.adoc) and
[boundary inventory](../../workflow/lifecycle-failure-inventory.md) for the fixed
contract and per-boundary reconciliation.

## Presentation and compatibility

`__main__.py` renders validated operation context in human-readable workflow and
setup summaries. Existing setup counts, timing, phase summaries and evidence paths
remain. JSON requires explicit opt-in and adds `operation_result` without replacing
legacy fields; setup retains its installation-plan preamble before JSON output.
Completed results retain exit 0, unsuccessful returned statuses exit 1, and missing
consent/confirmation exit 2. Verified recovery keeps completed/exit 0. Installer
child exits, timeout 124 and interruption 130 remain unchanged.

Safe failure values contain no raw exceptions, commands, credentials or process
output. Intentional diagnostic corrections omit worker identities from gateway
timeouts, resource names from missing Portainer endpoint errors and raw OS messages
from storage errors. Existing numeric HTTP status and safe static messages remain.

## Coverage and limits

Adapters preserve available LXC failure hints, typed configuration/storage failures,
and HTTP/process failures. Existing domain facts retain their available collapsed
classifications; they do not gain invented executable/permission detail. Endpoint
readiness keeps endpoint statuses in verification evidence while the common result
uses `verification_failed`.

The accepted inventory excludes unreachable default-lifecycle repositories, optional
command-repository execution, legacy Docker CLI construction and separate diagnostic
commands. Existing domain secret-manifest validation, safe endpoint facts and
transparent delegation retain their contracts. New retry, rollback and idempotency
policy belongs to ARCH-03.13 / #356.

## Migration and evidence

The [active workflow](../../workflow/workflow.md) records the seven implementation slices and their checkpoint history.
Deterministic tests include `tests.application.ports.test_operation_result`,
`tests.application.services.shared.test_operation_results`,
`tests.infrastructure.adapters.exceptions.test_operation_failure_mapping`,
`tests.test_package_entrypoint` and `tests.test_classic_update_cli`, together with
the inventory's adapter and workflow suites. Exact commands, results and requirement
coverage are maintained in `.tiny-swarm/evidence/issue-355/`.

The accepted decision preserves layer contracts, lifecycle orchestration, process
execution, Classic update and installer reporting decisions. S355-07 architecture checks, local quality (2259 tests; 18 exclusions) and the
independent issue completion audit passed. All15 requirements are evidenced in
`.tiny-swarm/evidence/issue-355/completion_audit.md`. No live or external
verification is claimed.
