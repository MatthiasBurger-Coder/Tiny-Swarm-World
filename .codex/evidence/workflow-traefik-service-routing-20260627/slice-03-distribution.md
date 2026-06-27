# Slice 03 Distribution

Workflow ID: `workflow-traefik-service-routing-20260627`
Slice ID: `03`
Slice title: Service Access Links, Evidence And Live Suite Structure

Affected areas:

- service-access dashboard
- compose routing labels
- integration tests
- live-suite static tests
- security redaction review

Chosen execution mode: sequential.

Selected streams:

- backend
- runtime
- tests
- security

Real subagents used: no.

Fallback role-based review used: yes.

Git worktrees used: no.

Expected touched files/directories:

- `infra/config/compose/service-access/**`
- `infra/config/compose/swagger/docker-compose.yml`
- `infra/config/compose/pulsar/docker-compose.yml`
- `tests/integration/test_service_access_routing.py`
- `tests/live/test_post_install_browser_live.py`

Conflict risks:

- Dashboard link parser previously accepted localhost links only.
- Pulsar broker TCP must not be treated as HTTP.

Quality gates to run:

- `PYTHONPATH=src python -m unittest tests.integration.test_service_access_routing`
- `PYTHONPATH=src python -m unittest tests.live.test_post_install_browser_live`

Consolidation plan:

- Add host-based Traefik labels for HTTP services and keep live checks
  default-skipped.

Parallelization decision:

- Rejected because the dashboard, compose labels and tests share route
  semantics.
