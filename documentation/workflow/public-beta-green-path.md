# Public-Beta Green-Path Acceptance Gate

Gate ID: `PUBLIC-BETA-GREENPATH-20260813`

Status: `BLOCKED_LIVE_CONSENT_MISSING`

This is the concrete acceptance specification for the Public-Beta gate. It is
not a live result and it does not authorize infrastructure mutation by itself.
The canonical evidence format is
[`live-greenpath-evidence-contract.md`](../evidence/live-greenpath-evidence-contract.md).

## Entry conditions

The run may start only when all of the following are recorded:

- explicit operator consent scoped to the target, scenario and reset/update
  behavior;
- a disposable or recoverable native Linux or WSL2 host;
- required Incus/LXC, Docker, Swarm, network, TLS, operator-secret and artifact
  prerequisites;
- a clean repository commit and selected profile;
- evidence directory ownership/permissions and redaction checks;
- the independent live-evidence reviewer and rollback owner.

Without consent or a required prerequisite the gate is
`LIVE_CONSENT_MISSING` or `LIVE_PREREQUISITE_MISSING` and stops before
mutation.

## Required scenario matrix

Public Beta requires all six cells when both host classes are in scope:

| Host | A — Fresh install | B — Reconcile/re-run | C — Existing-install update |
|---|---|---|---|
| Native Linux | required | required | required |
| WSL2 | required | required | required |

Scenario A starts from the defined clean-host baseline. Scenario B repeats the
same operation on the unchanged installation and proves idempotence/no drift.
Scenario C updates an existing installation and records readiness, rollback and
post-update evidence. A skipped cell is not a pass.

## Ordered green path per cell

1. Host classification and read-only preflight.
2. Incus/LXC nodes and Docker Engine readiness.
3. Docker Swarm initialization or existing-state verification.
4. Network, manager-profile ingress and Traefik HTTPS readiness.
5. Secret references, external secret readiness and redaction check.
6. Nexus/artifacts and image provenance.
7. Jenkins, SonarQube, Apache Pulsar and Swagger readiness.
8. Service Access route and browser/readiness verification.
9. Secure Traefik dashboard verification: TLS, hostname, authentication,
   unauthenticated rejection, no `api.insecure`, no extra dashboard port and
   Service Access preservation.
10. Readiness summary, evidence redaction, checksums, independent review and
    cleanup/rollback result.

Dependent phases stop after a refusal, block, resource gate, failed prepare,
failed apply or failed verify. Retries are bounded and exhausted retries keep
the failure state.

## Pass criteria

The gate is PASS only when every required scenario cell has redacted evidence
with `LIVE_VERIFIED` for all required live checks, no required service is
resource-gated/degraded, the secure admin surface is verified, checksums and
independent review are present, and cleanup/reconcile/update semantics are
successful. External quality systems require their own observable
`EXTERNAL_GATE_VERIFIED` result.

Any missing consent, missing host cell, raw secret, failed/blocked phase,
missing checksum/review, missing second run or unavailable external result
keeps the gate BLOCKED/INCOMPLETE. No local quality-gate result can replace a
live or external result.

## Current disposition

The repository contains the implementation, traceability maps, evidence
contract, manuals and local quality evidence. No Incus, Docker, Swarm,
compose, DNS, browser or bootstrap command was run for this gate. Therefore
all six cells are currently `LIVE_CONSENT_MISSING`, and #120 remains blocked
until an authorized run and fresh audit on `main` exist.
