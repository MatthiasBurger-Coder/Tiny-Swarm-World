# Issue #183 Changed Files

## Product implementation

* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/command/`
* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/swarm/`
* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/docker/`
* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/services/`
* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc/images/`
* `src/tiny_swarm_world/infrastructure/adapters/clients/lxc_swarm_runtime.py`
* `src/tiny_swarm_world/infrastructure/adapters/preflight/artifact_readiness.py`
* `src/tiny_swarm_world/infrastructure/composition.py`

## Tests

* `tests/infrastructure/adapters/clients/lxc/`
* `tests/infrastructure/adapters/clients/test_lxc_swarm_runtime.py`
* `tests/infrastructure/test_lxc_runtime_logging.py`
* `tests/infrastructure/test_composition.py`
* `tests/architecture/test_lxc_runtime_boundaries.py`
* `tests/live/browser_e2e_contract.py`
* `tests/live/test_post_install_browser_live.py`

## Governance and documentation

* `.tiny-swarm/evidence/solid-lxc-swarm-runtime/`
* `.codex/evidence/slice-01` through `slice-07` distribution/consolidation
  records
* `documentation/arc42/05_building_blocks.adoc`
* `documentation/arc42/05_analysis/responsibility-separation-analysis.md`
* `documentation/arc42/11_risks_and_debt.adoc`

No application port files, live infrastructure state, credentials, or generated
live evidence payloads were changed.
