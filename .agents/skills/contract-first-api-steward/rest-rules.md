# REST Rules

## Required REST Contract Fields

- endpoint path
- HTTP method
- request schema
- response schema
- status codes
- error model
- authentication and authorization expectation
- idempotency expectation
- pagination or streaming behavior when applicable
- consumer list

## Rules

- REST adapters translate external HTTP input into application requests.
- Domain and application packages must not depend on REST framework APIs.
- REST DTOs are adapter contracts, not shared domain models.
- Error responses must be stable, documented and testable.
- Breaking path, method, status or schema changes require compatibility review.

## STOP Rules

Stop when:

- path or method is unclear;
- request or response shape is undocumented;
- error model is missing;
- consumers are unknown for a breaking change;
- DTOs are planned as shared Java modules between services.
