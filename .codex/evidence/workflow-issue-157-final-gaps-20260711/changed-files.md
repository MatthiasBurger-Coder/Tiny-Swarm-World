# Changed Files

Status: `COMPLETE_THROUGH_SLICE_06_PRE_FINAL_HEAD`

## Product And Architecture

- `src/tiny_swarm_world/domain/ingress/desired_state.py`
- `src/tiny_swarm_world/application/ports/repositories/port_effective_access_model_repository.py`
- `src/tiny_swarm_world/application/ports/repositories/port_routing_evidence_repository.py`
- `src/tiny_swarm_world/application/services/deployment/__init__.py`
- `src/tiny_swarm_world/application/services/deployment/write_effective_access_model_evidence.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py`
- `src/tiny_swarm_world/infrastructure/adapters/repositories/routing_evidence_local_repository.py`
- `src/tiny_swarm_world/infrastructure/composition.py`

## Tests And Fixtures

- `tests/application/services/deployment/test_write_effective_access_model_evidence.py`
- `tests/domain/ingress/test_desired_state.py`
- `tests/infrastructure/adapters/repositories/test_compose_file_repository_yaml.py`
- `tests/infrastructure/adapters/repositories/test_routing_evidence_local_repository.py`
- `tests/infrastructure/test_composition.py`
- `tests/integration/routing_contract.py`
- `tests/integration/test_optional_service_routing.py`
- `tests/live/browser_e2e_contract.py`
- `tests/live/test_observability_browser_e2e.py`
- `tests/live/test_post_install_browser_live.py`
- `tests/live/test_tiny_swarm_app_browser_e2e.py`
- `tests/support/effective_access_model_fixture.py`

## Documentation

- `documentation/arc42/05_building_blocks.adoc`
- `documentation/arc42/06_runtime_view.adoc`
- `documentation/arc42/07_deployment_view.adoc`
- `documentation/arc42/10_quality_requirements.adoc`
- `documentation/arc42/11_risks_and_debt.adoc`
- `documentation/system/live-operation-surfaces.adoc`
- `documentation/user_guide/installation.adoc`
- `documentation/user_guide/usage.adoc`
- `documentation/user_guide/troubleshooting.adoc`
- `documentation/workflow/workflow.md`
- `documentation/workflow/context-pack.md`
- `documentation/workflow/context-pack.json`

## Evidence

- `.codex/evidence/workflow-issue-157-final-gaps-20260711/**`
- `.tiny-swarm/evidence/issue-157-final-gaps-20260711/**` (ignored local
  issue-completion package)

## Deliberately Unchanged

- Committed `services.yml`, `ports.yaml`, compose configuration, and the
  default dashboard HTML.
- ADRs, provider/Swarm setup, direct port publication, DNS/TLS lifecycle,
  messaging, Infisical bootstrap, Kubernetes, and CI configuration.
- `.tiny-swarm-world/local/live-installation.env` was neither read nor changed.

## Slice 06 Publication And Remediation

- `src/tiny_swarm_world/infrastructure/adapters/repositories/compose_file_repository_yaml.py`
  received a behaviorally equivalent tuple-based prefix check for SonarCloud
  rule `python:S8513`.
- `.codex/evidence/workflow-issue-157-final-gaps-20260711/slice-06-distribution.md`
  and `slice-06-consolidation.md` record publication ownership and results.
- The five required publication-status evidence files record observed PR,
  quality, SonarCloud, review, and live-E2E state.

No other product, test, configuration, documentation, ADR, CI, or live file
changed in Slice 06.
