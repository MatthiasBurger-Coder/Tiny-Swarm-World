# Slice 05 Distribution Decision

Workflow id: `workflow-replace-rabbitmq-with-apache-pulsar`

Slice id: `S05`

Slice title: Update service-access and dashboard

Affected areas:

- documentation
- tests
- runtime

Chosen execution mode: sequential

Selected streams:

- runtime
- documentation
- tests

Real subagents used: no

Fallback role-based review used: yes

Git worktrees used: no

Expected touched files/directories:

- `infra/config/compose/service-access/nginx/default.conf`
- `infra/config/compose/service-access/dashboard/index.html`
- `tests/integration/test_post_install_browser_live.py`
- `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py`
- `documentation/system/live-operation-surfaces.adoc`
- `.codex/evidence/slice-05-distribution.md`
- `.codex/evidence/slice-05-consolidation.md`

Conflict risks:

- Pulsar standalone has an Admin API, not a RabbitMQ-style management UI.
- Service-access must not expose host port `8080` for Pulsar.
- Browser/live tests are opt-in and may be skipped unless live environment
  variables are set.

Quality gates to run:

- `PYTHONPATH=src python3 -m unittest tests.integration.test_post_install_browser_live`
- `python3 tools/quality_gate.py quality`

Consolidation plan:

- Replace `/rabbitmq` service-access route with `/pulsar`.
- Replace RabbitMQ dashboard entry with Pulsar Admin API.
- Replace RabbitMQ browser integration login check with Pulsar Admin API HTTP
  reachability.
- Update static dashboard tests and live-operation docs.

Parallelization decision:

- Rejected. Dashboard HTML, NGINX route, and tests reference the same user-facing
  route and must change together.
