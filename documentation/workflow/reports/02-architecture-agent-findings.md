# Architecture Agent Findings

The requested visibility goal is valid, but copying `PortUI` injection into
every setup and platform service would weaken architecture boundaries.

Architecture direction:

- Application services may emit structured progress events.
- Concrete terminal UI, curses behavior, `FactoryUI`, `LinuxUI`, and
  `LoggerFactory` stay in infrastructure.
- Composition wires a composite sink that sends progress to both `PortUI` and
  logs.
- Domain remains independent from logging and UI.

Stop conditions:

- Application imports infrastructure UI or logging modules.
- `PortUI` becomes a required constructor dependency for core setup/platform
  services.
- Logs or UI expose raw command output, credentials, tokens, environment
  payloads, or host-specific data.
- Validation requires live LXC, Incus, Docker, Swarm, compose, Portainer,
  Nexus, Jenkins, RabbitMQ, or SonarQube without explicit approval.

Slice 01 disposition:

- `arc42 review-required`: closable when `06_runtime_view` and
  `10_quality_requirements` record the planned progress behavior explicitly.
- ADR: not required for Slice 01.
