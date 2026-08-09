# Issue #156 Test and Evidence Results

Baseline: `ecdc71d94a72530905ecb0a41d2845921ad6debb`.

## Targeted verification

Command:

```text
PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml tests.integration.test_optional_service_routing
```

Result: `PASS` — 58 tests, 3.446 seconds.

The repository test output included an expected evidence-write diagnostic for
an optional deployment-input path, but the test process exited zero and all 58
tests passed. No live deployment, Docker, LXC, Incus, Swarm or networking
command was run.

## Static trace

- Registry: `infra/config/ports.yaml:51-337`.
- Typed registry loading: `src/tiny_swarm_world/infrastructure/adapters/repositories/port_registry_yaml_repository.py:23-43`.
- Compose resolution: `src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py:93-120`.
- Direct publisher map: `compose_file_repository_yaml.py:732-748`.
- Unresolved service-access publishers: `infra/config/compose/service-access/docker-compose.yml:17-24`.
- Effective access projection: `src/tiny_swarm_world/domain/ingress/desired_state.py:211-277` and the existing redacted JSON evidence model.

## Quality state

`git diff --check`: `PASS` before evidence authoring. The required full
`python3 tools/quality_gate.py quality` result is not claimed by this slice.

