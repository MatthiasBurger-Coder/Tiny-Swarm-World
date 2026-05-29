# Report 03: Architecture Baseline

## Architecture Status

The current architecture already accepts `lxc_native` through LXD or Incus as
the default provider direction. Platform init can create LXC nodes, but
provider-native Docker install and Docker Swarm initialization are still
documented as incomplete or blocked.

## Boundary Decision

The new workflow remains a Platform workflow:

- Platform owns LXD/Incus readiness, LXC node lifecycle, Docker install, Swarm
  init/join, and platform verification.
- Artifacts owns registry/publication behavior and is not implemented here.
- Deployment owns service-stack behavior and is not implemented here.
- Console/status UI only receives terminal status vocabulary and reporting
  consistency if required.

## ADR Impact

No new ADR is required to create this workflow. A new ADR becomes required
during execution if implementation needs any of these changes:

- privileged containers as a default;
- broad host mounts;
- host package installation or daemon repair;
- non-interactive live consent;
- material changes to evidence or credential semantics.

## Frontend Assessment

No browser frontend or React work is in scope. The mandatory frontend role is
limited to recording that no React/TSX/JS/browser artifact should be created.
