# Changed Files — ARCH-03.06

- `src/tiny_swarm_world/application/ports/clients/port_swarm_stack_runtime.py`
  — documents the canonical application runtime port.
- `src/tiny_swarm_world/infrastructure/adapters/clients/docker_swarm_runtime.py`
  — adds the Docker Swarm port adapter.
- `src/tiny_swarm_world/infrastructure/composition_deployment.py` — wires the
  adapter around the LXC-backed transport.
- `src/tiny_swarm_world/infrastructure/composition_runtime.py` — exposes the
  adapter through the composition compatibility surface.
- `tests/infrastructure/adapters/clients/test_docker_swarm_runtime.py` —
  verifies success delegation and failure propagation.
- `tests/architecture/test_lxc_runtime_boundaries.py` — verifies port/adapter
  ownership.
- `documentation/arc42/05_analysis/arch-03-06-runtime-port-docker-swarm-adapter.md`
  — records the architecture decision.
