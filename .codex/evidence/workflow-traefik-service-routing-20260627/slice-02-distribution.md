# Slice 02 Distribution

Workflow ID: `workflow-traefik-service-routing-20260627`
Slice ID: `02`
Slice title: Gateway Port Authority And Route Model

Affected areas:

- backend/domain
- application preflight
- infrastructure compose rendering
- runtime static configuration
- tests

Chosen execution mode: sequential.

Selected streams:

- backend
- runtime
- tests
- architecture

Real subagents used: no.

Fallback role-based review used: yes.

Git worktrees used: no.

Expected touched files/directories:

- `src/tiny_swarm_world/domain/ingress/desired_state.py`
- `src/tiny_swarm_world/domain/preflight/setup_manifest.py`
- `src/tiny_swarm_world/application/services/platform/preflight_service.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py`
- `infra/config/services.yml`
- `infra/config/compose/traefik/docker-compose.yml`
- related tests

Conflict risks:

- Public ingress port change affects setup manifest, LXC proxy exposure and
  static preflight expectations.

Quality gates to run:

- Targeted domain/preflight/compose/platform tests.
- Full `python3 tools/quality_gate.py quality`.

Consolidation plan:

- Keep public ingress on `80/443`; classify old gateway high ports as
  diagnostic only.

Parallelization decision:

- Rejected because source and tests share the same gateway contract.
