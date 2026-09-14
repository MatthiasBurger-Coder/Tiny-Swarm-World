# ARCH-03.08 — Platform Lifecycle Orchestrator

Status: implemented 2026-09-13

Issue: #351

## Decision

Platform lifecycle dispatch is owned by the application-level
`PlatformLifecycleOrchestrator`. It accepts a typed
`PlatformLifecycleRequest` and returns the existing typed
`PlatformWorkflowResult`. Its `PlatformLifecycleWorkflows` dependency is a
small set of workflow ports; it does not construct providers, execute
commands, inspect configuration, or perform infrastructure I/O.

The orchestrator dispatches one request to exactly one existing use-case
workflow. Destructive workflows receive the optional confirmation explicitly;
all other workflows receive no mutation or confirmation concerns. Concrete
workflow construction remains in infrastructure composition.

## Compatibility

The CLI now delegates platform action selection to the orchestrator. Existing
workflow classes, action names, result statuses, confirmation guards and setup
phase ordering remain unchanged. Composition exposes the orchestrator through
the platform service bundle while retaining the existing workflow collection
for setup and compatibility consumers.
