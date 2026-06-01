# Architecture Agent Findings

The requested visibility goal is valid. The clarified requirement makes
method-flow logging a Shared cross-cutting architecture concern, so it requires
ADR coverage before broad implementation.

Copying `PortUI` injection or concrete logger construction into every setup and
platform service would still weaken architecture boundaries.

Architecture direction:

- Application services may emit structured progress events.
- Method-flow tracing is introduced through a cross-cutting trace contract, not
  manual concrete logger calls in every method.
- Concrete terminal UI, curses behavior, `FactoryUI`, `LinuxUI`, and
  `LoggerFactory` stay in infrastructure.
- Composition wires a composite sink that sends progress to both `PortUI` and
  logs.
- Domain remains independent from logging and UI.
- The trace module records safe method metadata for entry, returned, and raised
  events and correlates it with high-level progress.

Stop conditions:

- Application imports infrastructure UI or logging modules.
- `PortUI` becomes a required constructor dependency for core setup/platform
  services.
- Infrastructure decorators or logger factories are imported by domain or
  application modules.
- Method trace events include raw arguments, return payloads, command output,
  raw exception messages, stack traces, credentials, tokens, environment
  payloads, host-specific paths, or local IP addresses.
- Logs or UI expose raw command output, credentials, tokens, environment
  payloads, or host-specific data.
- Validation requires live LXC, Incus, Docker, Swarm, compose, Portainer,
  Nexus, Jenkins, RabbitMQ, or SonarQube without explicit approval.

Corrective disposition:

- ADR is required because method-flow logging is a cross-cutting module.
- `arc42 review-required`: closable when `06_runtime_view`,
  `09_architecture_decisions`, and `10_quality_requirements` distinguish
  workflow progress from method-level trace logging.
- Existing setup/platform progress slices remain valid partial progress but
  cannot be claimed as complete fulfillment of the clarified requirement.
