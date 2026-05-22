# Metrics Rules

## Service Metrics

- request count
- request duration
- error count
- dependency failures
- queue depth when applicable

## Worker Metrics

- job count
- job duration
- retry count
- failure count
- cancellation count
- resource pressure when applicable

## Forensic Flow Metrics

- analysis run count
- ingestion event count
- replay gap count
- unresolved evidence count
- projection update count

## Rules

- Avoid high-cardinality labels such as raw file paths, exception messages or user-provided repository URLs.
- Metrics must not expose secrets or sensitive source content.
- Metrics are diagnostics, not evidence.

## STOP Rules

Stop when metrics would leak sensitive values or when a critical worker/service flow has no diagnosable failure signal.
