# Live Evidence Map

Live checks are applicable to the Public-Beta product claim but were not
executed by this documentation workflow. The state is therefore explicit and
non-success.

| Live category | Required evidence | Current state | Handoff |
|---|---|---|---|
| Host | native Linux and WSL2 classification, consent record | LIVE_CONSENT_MISSING | #125 contract |
| Fresh install | preflight through nodes, Docker, Swarm, network, secrets, artifacts, services | LIVE_CONSENT_MISSING | Green-Path |
| Re-run/reconcile | second idempotent successful run with redacted evidence | LIVE_CONSENT_MISSING | Green-Path |
| Existing-install update | update result, rollback/readiness state and evidence | LIVE_CONSENT_MISSING | Green-Path |
| Traefik | TLS certificate summary, hostname resolution, secure dashboard route, auth behavior | LIVE_CONSENT_MISSING | #150 handoff; #125 |
| Service Access | browser-visible route and service links | LIVE_CONSENT_MISSING | #125; #129 |
| Secrets | reference names and redacted readiness only; no raw values | LIVE_CONSENT_MISSING | #123/#125 policies |
| Artifacts | Nexus/registry readiness and image provenance | LIVE_CONSENT_MISSING | #125 |
| Quality services | Jenkins, SonarQube and required quality result | LIVE_CONSENT_MISSING / EXTERNAL_GATE_UNAVAILABLE | #125/#120 |
| Evidence | correlation, timestamps, scenario, command/result summary, redaction and rollback state | LIVE_CONSENT_MISSING | #121/#125 |

The canonical admin-surface handoff is
[`live-greenpath-evidence-contract.md`](../evidence/live-greenpath-evidence-contract.md).
No row may be changed to `LIVE_VERIFIED` without executed, redacted evidence
for the actual scenario.
