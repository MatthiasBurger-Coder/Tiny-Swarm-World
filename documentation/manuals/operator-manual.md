# Operator Manual

This is the concise operator entry point. The canonical detailed instructions
remain in the [User Handbook](../user-handbook.adoc) and
[installation guide](../user_guide/installation.adoc).

## Before changing the host

Tiny Swarm World is Linux/WSL-only, Docker Swarm-first and LXC-native through
Incus. Read the [live-operation surface catalog](../system/live-operation-surfaces.adoc)
before any command that can mutate nodes, networking, Docker, Swarm or stacks.
The default quality gate does not perform those mutations.

## Install and operate

Use the [installation guide](../user_guide/installation.adoc), the
[operator configuration contract](../arc42/08_configuration/operator-configuration-contract.md)
and the [deployment view](../arc42/07_deployment_view.adoc). Preflight, reset
confirmation, explicit live consent and readiness results are separate gates;
a missing prerequisite is not a pass.

## Secrets and recovery

Use the [secret-handling policy](../security/secret-handling-policy.md) and
[security controls](../security/security-controls.md). Keep credentials and
private material outside committed documentation and evidence. For incidents
or failed mutation, follow [incident response](../security/incident-response.md)
and the recovery/rollback guidance in the [installation guide](../user_guide/installation.adoc).

## Verification status

Local tests and the quality gate prove repository behavior only. Live install,
TLS, DNS, browser and service readiness require the
[Live Validation Manual](live-validation-manual.md) and explicit consent.
