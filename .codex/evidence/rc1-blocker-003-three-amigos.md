# RC1_BLOCKER-003 — Three-Amigos Analysis

## Scenario

- Scenario: RC1-08 WSL2 RESTART RESILIENCE
- First failing operation: post-`wsl.exe --shutdown` platform reconcile
- Commit at observation: `27ce3960da98a9ba124fd3f9ff5e003b13e89c60`
- Branch: `feature/classic-public-beta-rc1-stabilization`
- Classification: `RC1_BLOCKER`

## Observed

The canonical reconcile command returned structured status `failed_to_apply`
for `swarm-manager` at `2026-08-23T13:36:56Z`–`13:37:24Z`. The Incus daemon
became fully active at `13:37:24Z`; the forwarding unit became active before
that, and the nodes were subsequently observed running. The failed lifecycle
transition therefore remained a real non-pass even though the platform later
converged through host startup.

## Four-role review

### Requirement Lead

Restart resilience requires the same managed nodes to return to a verified
ready state after WSL restart. A later automatic convergence cannot relabel
the failed reconcile as PASS.

### System Architect

The defect belongs at the existing LXC provider-readiness adapter boundary.
`composition.py`, service stacks, Docker Swarm state, and secrets are not the
cause and remain out of scope. The readiness contract must distinguish a
reachable CLI from a daemon that completed its early-start lifecycle.

### Python Automation Developer

Use Incus's existing read-only `incus admin waitready` command before the
existing `version` and `info` probes. Keep the wait bounded and reuse the
existing provider preflight runner; do not add a lifecycle start retry or a
blind sleep.

### Test / Evidence Reviewer

Add a regression assertion that `waitready` is the first probe and that a
waitready timeout stops before version/info. Run the full local quality gate,
then repeat the complete real restart scenario and record the result.

## Decision

Serial implementation is required because the WSL2/Incus target is shared.
No parallel work, workaround, waiver, skip, or manual node start is allowed.
The blocker remains open until the complete affected RC1-08 restart scenario
passes after the fix.
