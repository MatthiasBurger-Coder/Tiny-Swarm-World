# Three Amigos Review

## Requirement Engineer

Decision: accepted

Notes:

- RabbitMQ migration scope is verified as a platform service replacement for
  active inventory, preflight, deployment contracts, service access,
  configuration, tests, and documentation.
- The existing install greenpath must remain `./install.sh`.
- Remaining RabbitMQ references after implementation must be classified as
  historical documentation, migration evidence, deprecated compatibility note,
  or bug.

## System Architect

Decision: accepted

Notes:

- Apache Pulsar standalone is acceptable for the local development phase-1
  greenpath.
- Pulsar admin HTTP must not expose host port `8080`; use service-access or
  a non-conflicting external mapping such as `8087:8080` when required.
- Declarative inventory and service stack contracts remain the source of truth.
- No RabbitMQ compatibility mode or hidden fallback is allowed.

## Senior Tester

Decision: accepted

Notes:

- Slice execution must adapt existing RabbitMQ expectations to Pulsar instead
  of deleting tests.
- Unit tests must cover changed domain contracts, preflight behavior,
  configuration contracts, and service stack contracts.
- Compose/YAML and browser/service-access checks must be updated.
- Live greenpath evidence is required or must be explicitly documented as not
  executable in the current environment.

## Final Gate Decision

Decision: accepted

Required changes before implementation:

- None for Slice 01.
- Implementation slices must stop if baseline evidence reveals deep RabbitMQ
  application client coupling or any need to keep RabbitMQ as fallback.
