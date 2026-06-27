# Slice 01 Distribution

Workflow ID: `workflow-traefik-service-routing-20260627`
Slice ID: `01`
Slice title: Baseline Routing Contract Tests

Affected areas:

- backend/domain tests
- infrastructure repository tests
- live-suite static tests
- architecture/security review for default-skipped live checks

Chosen execution mode: sequential.

Selected streams:

- tests
- backend
- runtime static review
- security evidence review

Real subagents used: no.

Fallback role-based review used: yes. Senior Tester leads, with Senior
Requirement Engineer, Senior System Architect and Senior Python Automation
Developer review in this thread.

Git worktrees used: no.

Expected touched files/directories:

- `tests/domain/ingress/test_desired_state.py`
- `tests/domain/preflight/test_preflight_result.py`
- `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py`
- `tests/live/test_post_install_browser_live.py`
- `.codex/evidence/workflow-traefik-service-routing-20260627/**`

Conflict risks:

- Tests currently encode `10080/10443` as preferred ingress.
- Existing live static tests parse direct localhost links.

Quality gates to run:

- `PYTHONPATH=src python3 -m unittest tests.domain.ingress.test_desired_state`
- `PYTHONPATH=src python3 -m unittest tests.domain.preflight.test_preflight_result`
- `PYTHONPATH=src python3 -m unittest tests.infrastructure.adapters.repositories.test_compose_file_repository_yaml`
- `PYTHONPATH=src python3 -m unittest tests.live.test_post_install_browser_live`

Consolidation plan:

- Add failing/static tests first, then Slice 02 and Slice 03 satisfy them.

Parallelization decision:

- Rejected. Tests cover shared route and port contracts that must guide later
  implementation in order.
