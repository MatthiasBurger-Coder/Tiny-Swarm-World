# Architecture Findings

The current architecture already contains the right conceptual split:

* `init` and `reconcile` are non-destructive.
* `reset` and `destroy` are destructive and confirmation-gated.
* `setup run` orchestrates platform, artifacts and deployment phases.
* `install.sh` is a wrapper around `setup run --live`, not a reset wrapper.
* The default install profile is already `service-access`.
* Composition already contains service-access artifact and deployment target
  IDs, but the workflow must prove they are reached after reset before install
  success is reported.

Implementation must fill the blocked destructive workflow gap instead of
placing raw teardown commands in application services. Application code should
define ports and workflow behavior; infrastructure adapters should own LXD,
Incus, LXC and Docker command details.

The update/reconcile surface should remain in place. Fresh install should use
a destructive prelude only for `install.sh` or a dedicated reinstall path.
The destructive adapter must delete only configured or marker-verified Tiny
Swarm World managed resources, never every host LXC/Incus container.
