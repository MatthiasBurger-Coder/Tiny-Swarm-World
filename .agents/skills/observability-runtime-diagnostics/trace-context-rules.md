# Trace Context Rules

## Required Terms

- `correlationId`
- `traceId`
- `spanId`
- `parentSpanId`
- `analysisRunId`
- `runtimeSessionId`
- `incidentId`
- `serviceName`
- `workerName`
- `stepName`
- `phase`

## Rules

- Every external request receives or generates a `correlationId`.
- Service-to-service calls propagate trace context when available.
- Worker steps include worker and step identity.
- Analysis flows include `analysisRunId` when an analysis run exists.
- Runtime replay flows include `runtimeSessionId` or `incidentId` when available.
- Missing context must be represented explicitly, not fabricated.

## STOP Rules

Stop when:

- correlation owner is unclear;
- required context fields are silently dropped;
- unrelated correlation IDs are merged;
- runtime events would not be replayable due to missing stable identity.
