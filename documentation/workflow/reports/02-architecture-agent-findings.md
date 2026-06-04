# Architecture Findings

These findings record the workflow creation baseline before Slices 01-06 were
implemented. Later execution checkpoints supersede the stale implementation
status statements while preserving the original architecture rationale.

The current architecture already contains the right conceptual split:

* `init` and `reconcile` are non-destructive.
* `reset` and `destroy` are destructive and confirmation-gated.
* `setup run` orchestrates platform, artifacts and deployment phases.
* At workflow creation time, `install.sh` was a wrapper around
  `setup run --live` without a reset prelude.
* The default install profile is already `service-access`.
* Composition already contains service-access artifact and deployment target
  IDs, but the workflow must prove they are reached after reset before install
  success is reported.

Implementation needed to fill the blocked destructive workflow gap instead of
placing raw teardown commands in application services. Slices 02-04 implemented
that path with application ports and infrastructure-owned LXD/Incus/LXC
details.

The update/reconcile surface should remain in place. Fresh install should use
a destructive prelude only for `install.sh` or a dedicated reinstall path.
The destructive adapter must delete only configured or marker-verified Tiny
Swarm World managed resources, never every host LXC/Incus container.
