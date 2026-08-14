# Live Evidence Map

Live checks are applicable to the Public-Beta product claim but were not
executed by this documentation workflow. The state is therefore explicit and
non-success.

| Requirement IDs | Live category | Required evidence | Current state | Handoff |
|---|---|---|---|---|
| REQ-124-21 | Host | native Linux and WSL2 classification, consent record | LIVE_CONSENT_MISSING | #125 evidence contract |
| REQ-124-21 | Fresh install | preflight through nodes, Docker, Swarm, network, secrets, artifacts, services | LIVE_CONSENT_MISSING | #125 contract; Green-Path |
| REQ-124-21 | Re-run/reconcile | second idempotent successful run with redacted evidence | LIVE_CONSENT_MISSING | #125 contract; Green-Path |
| REQ-124-21 | Existing-install update | update result, rollback/readiness state and evidence | LIVE_CONSENT_MISSING | #125 contract; Green-Path |
| REQ-124-22 | Traefik | TLS certificate summary, hostname resolution, secure dashboard route, auth behavior | LIVE_CONSENT_MISSING | #125 evidence contract |
| REQ-124-22 | Service Access | browser-visible route and service links | LIVE_CONSENT_MISSING | #125 evidence contract |
| REQ-124-17 | Secrets | reference names and redacted readiness only; no raw values | LIVE_CONSENT_MISSING | #125 contract; #123 policy |
| REQ-124-21 | Artifacts | Nexus/registry readiness and image provenance | LIVE_CONSENT_MISSING | #125 contract; Green-Path |
| REQ-124-21 | Quality services | Jenkins and service quality readiness | LIVE_CONSENT_MISSING | #125 contract; Green-Path |
| REQ-124-23 | External gate | SonarQube and required external quality result | EXTERNAL_GATE_UNAVAILABLE | #120/release review |
| REQ-124-06, REQ-124-10 | Evidence | correlation, timestamps, scenario, command/result summary, redaction and rollback state | LIVE_CONSENT_MISSING | #125 contract |

The canonical admin-surface handoff is
[`live-greenpath-evidence-contract.md`](../evidence/live-greenpath-evidence-contract.md).
No row may be changed to `LIVE_VERIFIED` without executed, redacted evidence
for the actual scenario.
