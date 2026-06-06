# Senior System Architect Findings

## Summary

The change belongs in the LXC-native platform boundary. Expected proxy state
must be profile-level desired state, while direct instance-level devices remain
strict drift evidence.

## Boundary Guidance

* Domain may hold typed proxy/profile desired-state value objects.
* Application services may orchestrate ports and produce verification results.
* Infrastructure adapters own `incus` and `lxc` command syntax and output
  parsing.
* Composition owns concrete adapter construction.
* Entry-point changes stay limited to workflow taxonomy and dispatch.

## Architecture Risks

* Placing manager-only proxy devices in the shared `docker-swarm` profile would
  leak manager ingress behavior to workers.
* Allowing direct instance proxy devices in normal drift checks would weaken a
  safety contract.
* Repair must not become a hidden side effect of reset, reinstall, init,
  reconcile, or expose.

## arc42 Impact

Update runtime and deployment views after implementation because current docs
describe manager-gateway proxy configuration before the expected manager-profile
model exists.

## Decision

`READY_FOR_WORKFLOW`.
