# ARCH-03.14 — Runtime conditional ownership

Status: implemented locally for issue #357.

## Inventory and relocation

A search of `src/tiny_swarm_world/application/services` for Docker, Podman,
Kubernetes, Incus, LXC, WSL, Linux, runtime, platform, provider and profile
conditionals found no Docker/Podman/Kubernetes switch in a general application
workflow. The host preparation service was the general workflow that selected
between native Linux and WSL2 adapters. `composition_platform.py` now binds
those environment kinds to lazy adapter factories. The application service
looks up a binding and retains the existing unsupported-host result and live
consent guard. Adapter construction still occurs only for the selected host.

## Remaining justified conditionals

| Location | Owner | Reason |
|---|---|---|
| `application/services/platform/runtime_profile.py` | Capability policy | Resolves a supported managed LXC backend from explicit preference and observed availability; returns unsupported or unavailable status without fallback. |
| `application/services/platform/node_provider_selection.py` | Provider policy | Rejects unsupported provider intent and readiness mismatches before node mutation. These are safety checks on a typed selection, rather than runtime command dispatch. |
| `application/services/network/host_integration.py` | Network diagnostics and repair policy | WSL2 and native Linux produce different diagnostic sections. WSL NAT repair is valid only for WSL2; Incus and forwarding repair are separately selected operator targets. The application holds the dry-run, applicability and safety decisions while the ports perform runtime-specific inspection and mutation. |
| `application/services/platform/preflight_service.py` | Preflight applicability policy | WSL resource and Windows bridge checks apply only to WSL2. The branches suppress irrelevant checks on native Linux and retain the supported-host and bridge-required guards. |
| `application/services/platform/host/evaluate_project_filesystem.py` | Filesystem safety policy | Unsupported host kinds receive an unknown inspection without calling the filesystem inspector; supported hosts use its port. |
| `application/services/network/socat/socat_manager.py` | Legacy WSL Socat-specific use case | WSL Socat plans are emitted only for the WSL Linux runtime. This module is already technology-specific, so the branch is outside a runtime-neutral workflow. Its command formatting remains a separate mixed-boundary exception for ARCH-03.21. |
| `application/services/platform/incus/` | Incus-specific application use cases | The service boundary itself is explicitly Incus-specific and coordinates its ports; it is not a switch in a neutral workflow. |
| `domain/host_environment.py` | Host classification policy | Pure signal classification determines supported hosts before any adapter runs. |

A new runtime family should be added through capability resolution and
composition bindings. Any new branch in a general application workflow needs
an explicit policy reason and regression coverage for Classic behavior.

## Verification scope

Unit tests cover native Linux and WSL2 routing, lazy construction, unsupported
hosts and consent. The composition regression verifies both bindings and that
only the selected factory is created. These tests use mocks and perform no live
host preparation.
