# AGENTS.md

Follow the project-wide instructions in `../AGENTS.md`.

Additional scope for `infra/`:

- Treat files under `infra/config` as product behavior, not as throwaway
  examples.
- Preserve service stack boundaries under `infra/config/compose` and
  `infra/compose`.
- Keep shell scripts runnable from their own location by resolving paths from
  `${BASH_SOURCE[0]}` instead of assuming a specific current working directory.
- Do not run live Multipass, Docker Swarm, netplan, Portainer, Nexus, Jenkins,
  RabbitMQ, SonarQube, or compose deployment commands unless the user explicitly
  asks for live infrastructure changes.
- Avoid embedding host-specific absolute paths, user names, IP addresses, or
  secrets in committed configuration.
