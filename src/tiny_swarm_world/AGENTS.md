# AGENTS.md

Follow the project-wide instructions in `../../AGENTS.md`.

Additional scope for `src/tiny_swarm_world/`:

- Keep Python package imports qualified with the project package, for example
  `from tiny_swarm_world.application...`,
  `from tiny_swarm_world.domain...`, and
  `from tiny_swarm_world.infrastructure...`.
- Keep domain modules free of application and infrastructure imports.
- Keep application modules free of concrete infrastructure imports; inject
  dependencies through `application/ports`.
- Put new interfaces under `application/ports` and concrete implementations
  under `infrastructure/adapters`.
- Put standard runtime wiring in `infrastructure/composition.py` and keep
  `__main__.py` as a thin entry point.
- Keep command, VM, network, deployment, and service-stack behavior testable
  without running LXD, Incus, LXC, Docker Swarm, netplan, or live service bootstrap
  commands.
