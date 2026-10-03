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

## Collaborator and evidence completeness (ARCH-03.22, #331)

`PreflightResult.completeness` exposes immutable collaborator availability,
missing collaborator names, applicable collaborators, STATIC/LIVE scope,
malformed report IDs and summary-persistence state. The complete setup builders
`build_preflight_service` and `_build_preflight_service_for_request` declare
`STANDARD_SETUP`. Direct construction and the intentionally narrower post-install
builders declare `CUSTOM`. Missing collaborators in standard setup add a blocking
`PREFLIGHT-COLLABORATORS` check. Custom omissions retain legacy check-status
compatibility, but are visible in the completeness contract.

Resource inspection applies to WSL2. Filesystem evaluation applies to static and
live qualification. Filesystem authorization, secret-storage inspection and
artifact-source readiness apply to accepted live qualification. Availability
is reported even for collaborators outside the current run's scope, so a static
pass cannot hide incomplete live wiring. Evidence-writer availability is reported
separately from operational qualification.

`passed`, `status` and `failed_checks` retain their existing meaning. The additive
`executed_checks_passed` excludes synthetic wiring and summary-persistence failures.
`qualified` additionally requires coverage of applicable collaborators and no
malformed inspector reports. It qualifies only the reported scope. A custom result
may therefore have `passed=True` and `qualified=False`. Standard setup remains
blocking when its wiring is incomplete; existing mutation guards consume `passed`.

An inspector with absent methods or a return value outside `HostResources` /
`MemoryPressureReport` produces a mandatory failure with classification
`malformed_inspector_output`. Exceptions raised unexpectedly by an inspector still
propagate. An accepted live filesystem override without an authorizer fails before
runtime checks; static override evaluation remains read-only. The protected
filesystem authorizer continues to block when override evidence cannot be stored.

Summary persistence is `NOT_REQUESTED` for static or unaccepted-consent runs,
`MISSING_WRITER` when live summary storage has no callable writer, `STORED` only
after the write succeeds, and `FAILED` for expected `OSError` / `ValueError` writes.
Expected write failures retain every existing check and append the existing
`PREFLIGHT-EVIDENCE` failure without retrying or recursively writing. Unexpected
write exceptions still propagate. A stored failed-check report can be complete
evidence of failure; a stored partial/custom report with missing collaborators or
malformed report output cannot be complete evidence. `evidence_complete` requires
all reported collaborators and successful summary persistence, independently of
executed-check success. It describes this preflight summary, not successful
execution of later checks skipped by a safety stop or a release evidence package.

Both JSON presentations include the same completeness metadata and explicitly
report `release_evidence_acceptance=NOT_EVALUATED`. Local preflight qualification,
including stored complete summaries, never grants RC1/release acceptance. Existing
release reviewers and live-validation evidence requirements remain authoritative.

Regression coverage: `test_preflight_completeness`, existing preflight/authorizer
regressions, standard/post-install composition checks and the architecture test
that exercises the actual pre-apply guard through `PortPlatformPreflight`.
