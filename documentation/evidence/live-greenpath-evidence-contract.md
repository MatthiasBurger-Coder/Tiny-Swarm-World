# Canonical Live Green-Path Evidence Contract

Issue #125 defines the evidence bundle for a future authorized Public-Beta
run. This document is a contract, not a result. Its current state is
`PLANNED`; no live deployment, DNS mutation, browser check or credential test
was executed while authoring it.

## Bundle and scenario contract

Each run writes only to an ignored local evidence root such as
`.tiny-swarm-world/evidence/live-greenpath/<run-id>/`. The run must identify:

- a unique `run_id`, UTC start/end timestamps and repository commit;
- explicit operator consent, host class (`native_linux` or `wsl2`), target
  ownership and disposable/recoverable environment;
- scenario `A_fresh_install`, `B_reconcile_rerun` or `C_existing_update`;
- phase records for preflight, nodes, Docker Engine, Swarm, network/Traefik,
  secrets, artifacts, Jenkins, SonarQube, Pulsar, Swagger, Service Access,
  readiness and browser verification;
- per-phase state, bounded retry count, result classification, redacted
  summary, evidence file references and rollback/cleanup result. Each phase
  records `attempts`, `max_attempts`, `retryable`, `exhausted` and an explicit
  result classification;
- a two-level SHA-256 checksum chain: `checksums.sha256` hashes every redacted
  payload file and excludes checksum files, while
  `checksums.sha256.sha256` hashes `checksums.sha256`. The terminal hash file
  is deliberately not recursively self-hashed;
- independent reviewer identity, review timestamp, findings and final
  decision.

The minimum scenario matrix is:

| Scenario | Required run |
|---|---|
| A | Clean-host preflight through all required services and browser/readiness evidence. |
| B | Re-run/reconcile on the unchanged installation; prove idempotence and no drift. |
| C | Update an existing installation; prove update, readiness, rollback classification and evidence. |

Each scenario must be evaluated on native Linux and WSL2 when both hosts are
in scope. A missing host scenario is `LIVE_PREREQUISITE_MISSING`, never an
implicit pass.

## State semantics

Use the exact live states from
[`verification-state-policy.md`](../process/verification-state-policy.md):
`LIVE_NOT_APPLICABLE`, `LIVE_CONSENT_MISSING`,
`LIVE_PREREQUISITE_MISSING`, `LIVE_BLOCKED_BEFORE_MUTATION`,
`LIVE_FAILED_AFTER_MUTATION`, `LIVE_PARTIAL`, `LIVE_DEGRADED` and
`LIVE_VERIFIED`. Only `LIVE_VERIFIED` is a live success claim. A phase failure
must stop dependent phases and preserve its failure classification.

Each phase also records exactly one result classification independent of live
state: `passed`, `refused`, `blocked`, `resource-gated`, `failed-to-apply`,
`failed-to-prepare`, `failed-to-verify`, `partial` or `degraded`. Retryable
failures use bounded attempts; once `max_attempts` is reached, `exhausted` is
true and the phase remains failed/blocked rather than becoming a pass.

External results use the policy's `EXTERNAL_GATE_*` states. A local quality
gate does not become a SonarQube or external-gate result.

## Required admin-surface facts

The secure Traefik GUI evidence must include the secret-name reference without
its value, TLS certificate summary without private material, hostname
resolution, HTTPS/authentication response, unauthenticated rejection,
`api.insecure` absence, Service Access preservation and the outcome when a
required TLS or users secret is missing. The current repository-only evidence
for these facts is local/static; the live fields remain unverified until a
consented run supplies redacted data.

The reusable run shape is in
[`live-run-template.md`](live-run-template.md), the redaction contract in
[`redaction-rules.md`](redaction-rules.md), and the operator checklist in
[`live-smoke-checklist.md`](live-smoke-checklist.md).
