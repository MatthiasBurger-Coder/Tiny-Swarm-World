# Issue #184 — Remaining Risks

- Live Incus/LXD lifecycle behavior was not run; live validation remains
  opt-in, consent-gated and serialized.
- Browser, Selenium and SonarQube results were not observed and are not
  claimed as green.
- Typed serialized verification-evidence builders remain in the #191 workflow;
  this issue preserves the existing dictionary contract until that successor.
- The workflow chain remains serialized because later issues share LXC command,
  node, evidence, preflight, Swarm, service and composition locks.

These are documented residual risks, not open Issue #184 requirements.
