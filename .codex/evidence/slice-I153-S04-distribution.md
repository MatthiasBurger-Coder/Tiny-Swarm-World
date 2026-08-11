# I153-S04 Distribution and Handoff

Slice: Explain host/node distinction and installation order

Owner role: Senior System Architect

Secondary review roles: Senior Documentation Engineer, Linux Host Preparation,
Senior Requirement Engineer

Execution mode: explicit role-based fallback. Arc42 governance was applied to
the deployment-view wording; no ADR history was rewritten and no new decision
was invented.

## Implemented guidance

- Installation documentation now states the verified order from Linux/WSL and
  Incus readiness through managed nodes, node-local Docker, Swarm, routing,
  artifacts, deployment, and readiness verification.
- Host Docker is explicitly optional diagnostic/cache tooling, not the managed
  workload runtime.
- Arc42 deployment view records the same host-versus-managed-node Docker
  boundary and order.
- Handbook wording remains a concise pointer rather than a duplicate topology
  catalogue.

## Verification

```text
git diff --check
```

Result: `PASS`. Facts are sourced from the existing installation order,
provider ADR, deployment view, and current setup workflow documentation.
