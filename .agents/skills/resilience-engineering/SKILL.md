---
name: resilience-engineering
description: Use for resilience decisions involving timeouts, retries, exponential backoff, circuit breakers, bulkheads, idempotency, dead-letter handling, retry provenance, health checks, readiness/liveness, graceful degradation, failure cleanup, correlation IDs, observability, diagnostic redaction, and fail-fast versus recoverable errors across UI, services, workers, storage, CI, containers, parsers, and external tool execution.
---

# Resilience Engineering

## Purpose

Guide resilient system design without hiding failures, duplicating side effects, leaking secrets, or converting partial success into silent success.

Use this skill when a change touches external calls, asynchronous work, tool execution, queue or worker behavior, storage writes, user-visible failure states, health checks, diagnostics, cleanup, or degraded operation.

## Core Rules

1. Give every external call, process execution, network request, storage operation, worker lease, and long-running analysis step an explicit timeout.
2. Keep retries bounded by maximum attempts, total elapsed time, and cancellation or shutdown signals.
3. Use exponential backoff with jitter for retryable transient failures that can otherwise synchronize callers.
4. Use circuit breakers when a dependency can fail repeatedly and callers need fast rejection or degraded behavior.
5. Use bulkheads when one dependency, tenant, repository, worker pool, or expensive analysis stage can exhaust shared capacity.
6. Preserve idempotency for retried operations. Never retry non-idempotent operations unless an idempotency key or equivalent safety mechanism exists.
7. Record retry provenance: attempt number, operation name, correlation ID, failure category, delay, final outcome, and whether side effects may have occurred.
8. Do not silently ignore partial failures. Return, persist, or display explicit incomplete, degraded, failed, or unknown states.
9. Clean up after failures only inside verified ownership boundaries and report cleanup failures separately from the original failure.
10. Keep correlation IDs, request IDs, trace IDs, session IDs, and job IDs intact across retries, worker hops, logs, diagnostics, and dead-letter records when they are available.
11. Remove secrets, credentials, tokens, personal data, and unnecessary source content from diagnostics, logs, health output, and dead-letter payloads.
12. Keep resilience mechanisms observable through logs, metrics, events, status models, or test-visible results without making observability the source of truth.

## Decision Rules

### When To Retry

Retry only when all of these are true:

- The failure is transient or dependency availability is plausibly temporary.
- The operation is idempotent, read-only, or protected by an idempotency key, compare-and-set guard, lease token, deduplication key, or equivalent safety mechanism.
- The retry budget is bounded and cancellable.
- Retry attempts preserve provenance and correlation IDs.
- Duplicate execution cannot overwrite raw evidence, corrupt state, duplicate user-visible findings, or hide incomplete work.

### When Not To Retry

Do not retry when:

- The operation is non-idempotent and lacks an idempotency key or equivalent safety mechanism.
- Validation failed because the input is malformed, unauthorized, unsupported, missing, or semantically inconsistent.
- A dependency rejected the request permanently.
- The operation may have completed but the caller cannot prove whether side effects occurred.
- Retrying would execute untrusted code, duplicate evidence, overwrite raw input, leak secrets, or make ordering ambiguous.
- The retry would exceed the configured budget, shutdown deadline, worker lease, or user cancellation.

### When To Fail Fast

Fail fast when:

- Required configuration, schema, contract, dependency, workspace boundary, credential source, or executable path is missing or unverifiable.
- A precondition protects evidence integrity, security, filesystem safety, or irreversible side effects.
- Continuing would require guessing a field, status, task, table, graph label, file path, or external operation result.
- A degraded path is not explicitly defined and tested.

### When To Compensate

Compensate only when:

- A compensating action is explicitly defined for the operation.
- Ownership of the affected resource is verified.
- The compensation is safe to repeat or guarded by state.
- The compensation result is reported independently from the original failure.

Prefer explicit failed or pending-compensation states over pretending rollback succeeded.

### When To Cleanup

Clean up after failures when:

- The resource was created by the current operation, lease, worker, or session.
- The cleanup target is inside a verified allowed root or ownership boundary.
- Cleanup does not destroy evidence needed to diagnose the failure unless retention policy explicitly permits deletion.
- Cleanup failure can be represented without changing the original operation into success.

### When To Dead-Letter

Dead-letter when work cannot be completed after bounded retries or cannot be safely retried now, and future review or replay is useful.

Dead-letter records should include:

- operation name
- correlation or request ID
- job, session, workspace, or artifact ID when available
- failure category and sanitized message
- attempt count and final attempt timestamp
- idempotency key or deduplication key when available
- original payload reference, checksum, or sanitized payload subset
- next-review or retention expectation

Do not dead-letter secrets or full sensitive payloads unless policy explicitly allows encrypted or access-controlled storage.

### When To Expose Diagnostics

Expose diagnostics to users or callers when they help them take safe action:

- invalid input
- missing dependency
- timeout limit reached
- unavailable optional capability
- degraded mode
- incomplete result
- retry exhausted
- cleanup incomplete

Use stable categories and sanitized detail. Preserve full internal causes only in protected logs or test-visible diagnostic structures.

### When To Hide Diagnostics

Hide, redact, or generalize diagnostics when they contain:

- credentials, tokens, secret values, private URLs, local absolute paths, personal data, or proprietary source snippets
- dependency internals that increase attack surface
- raw payloads that are not needed for safe user action
- speculative causes that are not proven by the system

## Platform Guidance

### Frontend

- Set request deadlines or cancellation using the existing client pattern.
- Show loading, failed, partial, stale, and degraded states explicitly.
- Avoid infinite client retries and retry loops that survive navigation or logout.
- Preserve correlation IDs from responses or error envelopes for support flows.
- Do not show secrets, stack traces, local paths, or raw payloads in user-visible errors.

### Backend Services

- Separate validation errors from recoverable dependency failures.
- Keep resilience configuration explicit and testable.
- Keep framework-specific resilience wiring out of domain models.
- Prefer idempotency keys for command endpoints that clients may retry.
- Keep readiness and liveness meaningful: liveness checks process health, readiness checks dependency or capacity readiness needed to serve traffic safely.

### gRPC

- Use deadlines and cancellation propagation for client and server calls.
- Preserve request IDs, correlation IDs, schema versions, and session identifiers.
- Design retries around idempotency and response status semantics.
- Avoid retrying stream chunks or session creation unless deduplication is defined.
- Map transport failures separately from application diagnostics where the contract supports it.

### Workers

- Model worker leases, attempts, cancellation, retry budgets, and final failure states explicitly.
- Avoid duplicate work by using idempotency keys, artifact checksums, job attempt IDs, or lease tokens.
- Keep retry provenance with the job record.
- Dead-letter exhausted or unsafe work with sanitized diagnostic context.
- Release or expire leases without losing evidence of incomplete work.

### Git Operations

- Apply timeouts to clone, fetch, checkout, commit resolution, remote detection, and cleanup.
- Treat checked-out repositories as untrusted input.
- Do not run hooks, builds, parsers, analyzers, or repository scripts as part of checkout resilience.
- Preserve requested branch, requested commit, resolved remote, resolved commit, checkout mode, timeout, elapsed time, and diagnostics.
- Cleanup must stay inside verified workspace roots and must not hide checkout failure.

### Workspace Cleanup

- Track ownership, lease, status, cleanup policy, and cleanup result.
- Keep failed, cleaned, retained, and cleanup-failed states distinct.
- Avoid deleting evidence required for failure diagnosis unless retention policy says deletion is required.
- Make cleanup idempotent or guarded by verified state.

### Docker Containers

- Keep container-dependent workflows optional unless the project requires them.
- Use startup timeouts, health checks, readiness checks, and explicit teardown behavior.
- Treat container logs as sensitive diagnostics.
- Report unavailable Docker or failed health checks without weakening the normal quality gate.

### Persistence

- Make storage writes idempotent where retries are possible.
- Use stable identities, deduplication keys, transactions, compare-and-set guards, or append-only attempt records where appropriate.
- Preserve raw inputs, provenance, ordering, correlation IDs, and completeness markers.
- Do not overwrite primary evidence with retry summaries, generated diagnostics, or hypotheses.

### Parsers And External Tools

- Apply execution timeouts, resource limits, cancellation, and bounded output capture.
- Treat parser, analyzer, and tool failures as explicit diagnostics, not as absent evidence.
- Keep stdout, stderr, generated artifacts, checksums, tool version, query version, and completeness state where relevant and safe.
- Do not retry tool execution if it may mutate the input workspace or produce duplicate authoritative artifacts without a safe output identity.

### CI And Quality Gates

- Do not weaken quality gates to reduce runtime or hide flaky behavior.
- Retry infrastructure-only failures only when the CI policy allows it and the rerun remains observable.
- Keep dependency verification strict when required.
- Report skipped optional external checks with the reason.
- Keep generated artifacts, logs, reports, and metrics out of commits unless the task explicitly requires archival.

## Project Application Notes

For the current project, apply these generic resilience rules to:

- React UI
- Spring Boot services
- gRPC communication
- Git checkout workflow
- workspace lifecycle
- worker orchestration
- Joern execution
- parser execution
- BTM generation
- Analysis Store
- Docker Compose startup
- CI and quality gates

Preserve domain evidence semantics: runtime, static, graph, replay, report, and LLM-related failures must remain explicit and must not be converted into confirmed evidence, successful analysis, or hidden partial output.

## Validation Checklist

- Does every external call have a timeout?
- Are retries bounded by attempts, elapsed time, and cancellation?
- Is retry behavior observable?
- Are operations idempotent before they are retried?
- Is every non-idempotent retry protected by an idempotency key or equivalent safety mechanism?
- Is exponential backoff or jitter needed?
- Is a circuit breaker needed for repeated dependency failure?
- Is a bulkhead needed to protect shared capacity?
- Is dead-letter handling defined for exhausted or unsafe work?
- Is retry provenance captured?
- Is cleanup safe, bounded, idempotent, and inside verified ownership boundaries?
- Are partial failures explicit?
- Are secrets removed from logs, diagnostics, health checks, and dead-letter records?
- Are health checks meaningful?
- Do readiness and liveness checks answer different questions?
- Is degraded behavior defined and testable?
- Is fail-fast behavior used for unverifiable contracts, unsafe inputs, or missing required configuration?
- Are recoverable errors separated from validation, authorization, and contract errors?
- Is observability sufficient without treating logs or metrics as primary evidence?
