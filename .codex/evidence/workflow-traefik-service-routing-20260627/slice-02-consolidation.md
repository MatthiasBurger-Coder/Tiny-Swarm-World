# Slice 02 Consolidation

Workflow ID: `workflow-traefik-service-routing-20260627`
Slice ID: `02`
Slice title: Gateway Port Authority And Route Model

Stream results:

- Domain ingress public ports changed to `80/443`.
- Setup manifest now exposes Traefik HTTP/HTTPS as `80/443`.
- Compose rendering maps Traefik target ports to `traefik-http` and
  `traefik-https` instead of diagnostic API-gateway IDs.
- Service registry and Traefik compose publish `80/443`.
- Preflight no longer permits planned reassignment on occupied public Traefik
  ingress ports.

Accepted findings:

- `10080/10443` must remain diagnostic only where retained.
- Occupied `80/443` is a live-environment blocker, not a silent fallback.

Rejected findings:

- Keeping `10080/10443` as preferred public ingress was rejected because it
  contradicts Issue #157 and the accepted Traefik ADR.

Files changed per stream:

- `src/tiny_swarm_world/domain/ingress/desired_state.py`
- `src/tiny_swarm_world/domain/preflight/setup_manifest.py`
- `src/tiny_swarm_world/application/services/platform/preflight_service.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py`
- `infra/config/services.yml`
- `infra/config/compose/traefik/docker-compose.yml`
- related tests under `tests/domain`, `tests/application`, `tests/infrastructure`

Conflicts found:

- Old tests expected `10080/10443`; updated to the new authoritative ports.

Conflicts resolved:

- Platform preflight tests now assert blockers for occupied public ingress.

Tests executed:

- Targeted WSL test bundle: 125 tests, 8 skipped, passed.
- Platform preflight/exposure/verify targeted tests: 47 tests, passed.
- Full quality gate later passed.

SonarQube findings and fixes:

- Not run locally.

Documentation updates:

- Deferred to Slice 04.

Final integration decision:

- Accepted.
