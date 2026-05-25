# Requirement Clarification Gate

## Decision

```text
PROCEED_WITH_ACCEPTED_ASSUMPTIONS
```

Confidence: `86 percent`

## Normalized Requirement

Tiny Swarm World should migrate its default node provider from Multipass VMs to
managed LXC containers through LXD or Incus. Multipass remains available only as
an explicit legacy/fallback provider. Raw low-level LXC-only automation is not
the first implementation path.

## Classification

- functional requirement: default provider becomes `lxc_native`;
- architecture constraint: provider behavior must stay behind domain,
  application port, and infrastructure adapter boundaries;
- resilience requirement: fail closed when LXD/Incus readiness is missing,
  ambiguous, or unsupported;
- security requirement: container profile, daemon, socket, and host mutation
  choices must be explicit and redacted;
- quality-gate requirement: default gates remain mocked/static and must not run
  live LXD, Incus, Multipass, Docker, or network mutation commands;
- assumption: `Incu` means `Incus`.

## Three Amigos Findings

Senior Requirement Engineer:

- The request clearly changes product direction.
- EPIC and root governance currently mention Multipass, so Slice 01 must record
  the provider decision and update requirement sources.

Senior System Architect:

- The change affects Platform, setup, preflight, provider ports, infrastructure
  clients, command configuration, composition, and deployment documentation.
- No new undeclared application service directories should be introduced.

Senior Python Automation Developer:

- The safest path is a provider-neutral model and ports first, then LXD/Incus
  adapters, then setup integration.
- Existing Multipass code should be wrapped as legacy before removal.

Senior React Frontend Developer:

- No browser frontend scope exists.
- Console/status wording may need updates only after CLI semantics change.

Senior Tester:

- Required tests must cover provider selection, LXD/Incus readiness, missing
  backend, ambiguous backend, fail-closed setup, and explicit Multipass legacy
  selection.

## Open Questions

- Incus or LXD preference when both are installed and no explicit backend is
  configured.
- Accepted container profile for Docker Swarm-in-container.
- Whether WSL2 is a first live target or capability-gated secondary path.
- Final CLI flag naming for provider selection.

## Blocking Questions

```text
None for workflow authoring.
```

## Stop Conditions Carried Forward

- Do not run live infrastructure commands without explicit approval.
- Do not silently fall back to Multipass.
- Do not document LXD/Incus live success before evidence exists.
- Do not enable privileged containers or host mutation without explicit
  security and consent handling.
