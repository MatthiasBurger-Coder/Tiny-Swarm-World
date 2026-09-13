# ARCH-03.05 — Runtime Profile Resolution

Status: implemented 2026-09-13

Issue: #348

## Decision

`RuntimeProfileResolver` is the canonical owner for selecting the service
profile and managed runtime backend. It accepts a typed
`RuntimeProfileResolutionRequest` containing the validated service/provider
intent, detected host environment, supported backends, and currently available
backend capabilities. It returns a typed `ResolvedRuntimeProfile` with an
explicit resolution status and remediation.

Automatic backend selection follows the configured candidate order and only
selects an available supported backend. An explicit supported preference is
honored; an unsupported provider or unavailable candidate is returned as a
non-resolved result without provider fallback.

## Composition boundary

Infrastructure discovery remains responsible for determining which backend
executables are available. The legacy `_lxc_backend_for_provider_request`
composition helper now delegates the selection decision to the application
resolver. Existing platform and Classic Docker Swarm call paths therefore keep
their public inputs and Incus behavior while sharing one selection owner.

Equivalent requests are resolved by a pure deterministic application service;
the service does not inspect the filesystem, environment, execute commands, or
mutate runtime state.
