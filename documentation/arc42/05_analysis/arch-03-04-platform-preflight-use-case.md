# ARCH-03.04 — Platform Preflight Use Case

Status: implemented 2026-09-13

Issue: #347

## Boundary

Platform prerequisite validation is exposed to application workflows through
`PortPlatformPreflight`. The port accepts optional live-consent context and
returns the typed `PreflightResult`; it has no operation for applying platform
state.

`PreflightService` remains the concrete application implementation. Its
existing host, filesystem, dependency, resource, network, secret and runtime
checks are unchanged. Infrastructure composition constructs that implementation
and injects it into platform services. Platform and setup orchestration consume
the port, so deployment mutation is not a preflight dependency.

## Execution order and safety

```text
CLI / setup composition
        |
        v
PortPlatformPreflight.run(consent)
        |
        v
typed PreflightResult
        |
        +--> failed: stop before platform/deployment mutation
        |
        +--> passed: platform workflow may continue
```

Static preflight remains runnable without live consent. Live checks still
require the existing explicit consent and host/filesystem safety rules. No
Incus, Docker, Swarm, compose, bridge, or service bootstrap operation is
performed by the port or its unit tests.

## Compatibility

The existing `PreflightService` import and composition builder remain stable.
The new port is the type boundary used by `PlatformServices` and the platform
pre-apply guard, allowing focused fake implementations in tests and preventing
deployment adapters from being required to validate prerequisites.
