# Live Validation Manual

This manual describes the Public-Beta validation boundary. It is not a
live run report. No live success is claimed by the presence of these links.

## Authoritative contract

Use the [live green-path evidence contract](../evidence/live-greenpath-evidence-contract.md),
[run template](../evidence/live-run-template.md),
[redaction rules](../evidence/redaction-rules.md) and
[smoke checklist](../evidence/live-smoke-checklist.md). The
[verification-state policy](../process/verification-state-policy.md) defines
the exact live and external states.

## Required matrix

For each applicable host class, the authorized run must cover:

- A: clean fresh install;
- B: reconcile/re-run without drift;
- C: update of an existing installation with rollback classification.

The path includes native Linux and WSL2 where in scope, host preflight,
LXC/Incus nodes, Docker Engine, Swarm, network/Traefik, secrets, artifacts,
Jenkins, SonarQube, Pulsar, Swagger, Service Access, readiness and browser
checks. Missing consent or prerequisites stops the run before mutation or
records the policy failure state.

## Current status

The [RC1 decision](../release/rc1-decision.md) records acceptance for its named
September candidates. [Issue #363 final validation](../evidence/issue-363-final-validation-20261003.md)
records later native/WSL installation, authentication and lifecycle evidence.
Those dated results retain their executed revisions; they do not qualify the
current bootstrap changes or every supported host.

For a new applicable live run without explicit consent, use
`LIVE_CONSENT_MISSING`; missing prerequisites and failed/partial results retain
their own states. External quality results also require exact-candidate evidence.
Do not run live commands from the default local quality workflow. The
[bootstrap contract](../contracts/bootstrap.md) identifies remaining integration
and qualification work.
