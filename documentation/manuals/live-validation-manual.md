# Live Validation Manual

This manual describes the future Public-Beta validation boundary. It is not a
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

The Public-Beta Green-Path is currently `LIVE_CONSENT_MISSING`. TLS/DNS,
browser authentication, service readiness, fresh/reconcile/update behavior and
external quality results require executed redacted evidence. Do not run live
commands from the default local quality workflow.
