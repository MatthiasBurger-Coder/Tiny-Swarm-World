# AGENTS.md

Follow the project-wide instructions in `../AGENTS.md`.

Additional scope for `docker/`:

- Keep Python package imports in the existing top-level package style, for
  example `from application...`, `from domain...`, and `from infrastructure...`.
- Keep domain modules free of infrastructure imports.
- Put new interfaces under `application/ports` and concrete implementations
  under `infrastructure/adapters`.
- Keep command, VM, network, deployment, and service-stack behavior testable
  without running Multipass, Docker Swarm, netplan, or live service bootstrap
  commands.
