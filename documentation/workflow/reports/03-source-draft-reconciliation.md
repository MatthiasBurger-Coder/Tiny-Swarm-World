# Source Draft Reconciliation

The supplied draft is the source requirement, but the generated workflow is not
a verbatim copy. It was reconciled against current repository behavior and
subagent review.

## Preserved From Draft

- Native Linux and WSL2 must be separate setup paths.
- WSL1 and unknown hosts must fail before mutation.
- Sandbox results must not prove WSL2 behavior.
- `infra/swarm` must be analyzed as migration evidence.
- Multipass readiness must check more than executable presence.
- WSL2 networking must avoid hardcoded host addresses.
- Normal quality gates must not run live infrastructure.
- Real WSL2 console validation is required before claiming WSL2 live success.

## Refined From Draft

- Current code already has live-consent-gated Multipass readiness checks, so
  implementation extends existing preflight instead of creating a parallel
  preflight system.
- Proposed new application service directories were removed from the default
  plan to avoid architecture-test drift.
- `setup run` without `--live` is documented as consent-boundary evidence, not
  a dry-run installation pass.
- Static `--preflight` is not treated as proof of Multipass daemon, qemu driver,
  Docker Swarm, or WSL2 forwarding behavior.
- Live WSL2 preflight-blocked outcomes are distinguished from full installation
  success.
- Evidence collection is constrained by current safe-text and setup payload
  rejection rules.

## Deferred Or ADR-Gated

- Automatic host package installation.
- Automatic socket ownership or permission repair.
- Automatic `netsh` or `iptables` mutation.
- Non-interactive live consent.
- Any material change to evidence semantics.

## Replacement Decision

The prior active `documentation/workflow/**` content was regenerated because it
described the older `Stable Live Setup` workflow. This workflow is now the
active workflow for the current branch.
